import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert } from 'antd'
import { UserOutlined, LockOutlined, SafetyOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { useLoginMutation } from '@/store/api/usersApi'
import { setCredentials } from '@/store/slices/authSlice'

const { Title, Text } = Typography

const Login: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const [login, { isLoading }] = useLoginMutation()
  const [error, setError] = useState<string>('')

  const onFinish = async (values: { username: string; password: string }) => {
    setError('')
    try {
      const result = await login(values).unwrap()
      dispatch(setCredentials({ access_token: result.access_token, refresh_token: result.refresh_token }))
      navigate('/')
    } catch (err: any) {
      setError(err?.data?.detail || '登录失败，请检查用户名和密码')
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f2f5' }}>
      <Card style={{ width: 400, boxShadow: '0 4px 24px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <SafetyOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          <Title level={3} style={{ marginTop: 16, marginBottom: 4 }}>安全生产业务管理系统</Title>
          <Text type="secondary">Safety Production BMS</Text>
        </div>

        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}

        <Form onFinish={onFinish} autoComplete="off" size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={isLoading}>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login
