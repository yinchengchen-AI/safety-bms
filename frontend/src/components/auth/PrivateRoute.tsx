import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated, selectIsInitialized, selectUserPermissions, selectCurrentUser } from '@/store/slices/authSlice'

interface PrivateRouteProps {
  requiredPermissions?: string[]
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ requiredPermissions }) => {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const isInitialized = useSelector(selectIsInitialized)
  const permissions = useSelector(selectUserPermissions)
  const currentUser = useSelector(selectCurrentUser)
  const location = useLocation()

  if (!isInitialized) {
    return null
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  if (requiredPermissions && requiredPermissions.length > 0) {
    const hasPermission = currentUser?.is_superuser || requiredPermissions.every((p) => permissions.includes(p))
    if (!hasPermission) {
      return <Navigate to="/" replace />
    }
  }

  return <Outlet />
}

export default PrivateRoute
