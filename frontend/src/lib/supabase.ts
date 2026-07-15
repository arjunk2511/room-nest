import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Check if we are running in local dev mock auth mode
export const isMockAuth = !process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export function getMockUser() {
  if (typeof window !== 'undefined') {
    const email = localStorage.getItem('mock_user_email');
    if (email) {
      return { id: 'mock-uuid', email };
    }
  }
  return null;
}

export function setMockUser(email: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('mock_user_email', email);
    // The dev token will be passed in the Authorization header
    const token = email === 'admin@roomnest.online' ? 'dev_admin' : `dev_user_${email.split('@')[0]}`;
    localStorage.setItem('mock_user_token', token);
  }
}

export function getMockToken() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('mock_user_token') || 'dev_user';
  }
  return 'dev_user';
}

export function clearMockUser() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('mock_user_email');
    localStorage.removeItem('mock_user_token');
  }
}
export async function getAuthHeader() {
  if (isMockAuth) {
    return `Bearer ${getMockToken()}`;
  }
  const { data: { session } } = await supabase.auth.getSession();
  return session ? `Bearer ${session.access_token}` : '';
}
