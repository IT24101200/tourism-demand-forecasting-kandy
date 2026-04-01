-- 1. Create a table for User Profiles
create table if not exists public.user_profiles (
  id uuid references auth.users(id) on delete cascade not null primary key,
  email text not null,
  full_name text,
  role text check (role in ('Hotel Manager', 'Tour Operator', 'Government Official', 'Other')),
  hotel_name text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Turn on Row Level Security
alter table public.user_profiles enable row level security;

-- 3. Create Policies
-- Users can view their own profile
create policy "Users can view own profile" on public.user_profiles
  for select using (auth.uid() = id);

-- Users can update their own profile
create policy "Users can update own profile" on public.user_profiles
  for update using (auth.uid() = id);

-- 4. Create an auth trigger (Function) to automatically create a profile when a new user signs up
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.user_profiles (id, email, full_name, role, hotel_name)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'role',
    new.raw_user_meta_data->>'hotel_name'
  );
  return new;
end;
$$ language plpgsql security definer;

-- 5. Attach the trigger to the auth.users table
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
