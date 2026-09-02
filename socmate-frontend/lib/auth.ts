import { getCurrentUser, UserProfile } from './api';

/**
 * Calculate initials dynamically from a user's full name.
 * Ex: "Alex Mercer" -> "AM", "Jean Dupont" -> "JD", "Utilisateur" -> "U"
 */
export function getInitials(name: string): string {
  if (!name || name.trim() === '') return 'U';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return parts[0].substring(0, 2).toUpperCase();
}

export async function fetchSessionUser(): Promise<UserProfile> {
  const user = await getCurrentUser();
  return {
    ...user,
    avatarInitials: getInitials(user.name)
  };
}
