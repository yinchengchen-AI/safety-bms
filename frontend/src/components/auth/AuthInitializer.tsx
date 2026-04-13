import React, { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { setUser, logout, setInitialized, setPermissions } from '@/store/slices/authSlice'
import { useGetMeQuery } from '@/store/api/usersApi'

const AuthInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const dispatch = useDispatch()
  const { data: user, error, isLoading } = useGetMeQuery(undefined, { refetchOnMountOrArgChange: true })

  useEffect(() => {
    if (user) {
      dispatch(setUser(user))
      dispatch(setPermissions((user as any).permissions || []))
    } else if (error) {
      dispatch(logout())
    } else if (!isLoading) {
      dispatch(setInitialized())
    }
  }, [user, error, isLoading, dispatch])

  return <>{children}</>
}

export default AuthInitializer
