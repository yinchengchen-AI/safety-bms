import { useSelector } from 'react-redux'
import { selectUserPermissions } from '@/store/slices/authSlice'

export function usePermission(permission: string): boolean {
  const permissions = useSelector(selectUserPermissions)
  return permissions.includes(permission)
}

export function usePermissions(...permissions: string[]): boolean {
  const userPermissions = useSelector(selectUserPermissions)
  return permissions.every((p) => userPermissions.includes(p))
}

export function useAnyPermission(...permissions: string[]): boolean {
  const userPermissions = useSelector(selectUserPermissions)
  return permissions.some((p) => userPermissions.includes(p))
}
