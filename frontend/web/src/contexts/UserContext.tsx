import { createContext, useContext } from 'react';

export interface UserProfile {
  username: string | null;
  userRole: string | null;
  userId: string | null;
}

export const UserContext = createContext<UserProfile>({
  username: null,
  userRole: null,
  userId: null,
});

export function useUser(): UserProfile {
  return useContext(UserContext);
}
