-- 1. Drop existing check constraint on user_profiles
ALTER TABLE public.user_profiles DROP CONSTRAINT IF EXISTS user_profiles_role_check;

-- 2. Add new check constraint allowing 'System Administrator'
ALTER TABLE public.user_profiles 
  ADD CONSTRAINT user_profiles_role_check 
  CHECK (role IN ('Hotel Manager', 'Tour Operator', 'Government Official', 'Other', 'System Administrator'));

-- 3. Update existing admin user (it24101200@my.sliit.lk) to have the core Admin role
UPDATE public.user_profiles 
SET role = 'System Administrator' 
WHERE email = 'it24101200@my.sliit.lk';

-- 4. Create an RLS policy so the System Administrator can manage other profiles
CREATE POLICY "System Administrators can manage all profiles" ON public.user_profiles
  FOR ALL
  USING (
    (SELECT role FROM public.user_profiles WHERE id = auth.uid()) = 'System Administrator'
  )
  WITH CHECK (
    (SELECT role FROM public.user_profiles WHERE id = auth.uid()) = 'System Administrator'
  );
