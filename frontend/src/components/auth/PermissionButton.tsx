import React from 'react'
import { Button } from 'antd'
import type { ButtonProps } from 'antd'
import { usePermission } from '@/hooks/usePermission'

interface PermissionButtonProps extends ButtonProps {
  permission: string
  children?: React.ReactNode
}

export const PermissionButton: React.FC<PermissionButtonProps> = ({ permission, children, ...rest }) => {
  const has = usePermission(permission)
  if (!has) return null
  return <Button {...rest}>{children}</Button>
}
