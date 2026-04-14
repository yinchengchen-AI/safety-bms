import React, { useEffect, useState } from 'react'
import { Card, Form, Input, Button, Avatar, message, Row, Col, Upload } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { useSelector, useDispatch } from 'react-redux'
import { selectCurrentUser, setUser } from '@/store/slices/authSlice'
import { useUpdateMeMutation, useChangePasswordMutation, useGetMeQuery, useUploadAvatarMutation } from '@/store/api/usersApi'
import type { User } from '@/types'

const passwordPattern = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d\W_]{8,}$/

const Profile: React.FC = () => {
  const dispatch = useDispatch()
  const currentUser = useSelector(selectCurrentUser)
  const [basicForm] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const { refetch: refetchMe } = useGetMeQuery()
  const [updateMe, { isLoading: updating }] = useUpdateMeMutation()
  const [changePassword, { isLoading: changing }] = useChangePasswordMutation()
  const [uploadAvatar, { isLoading: uploadingAvatar }] = useUploadAvatarMutation()
  const [previewUrl, setPreviewUrl] = useState<string | undefined>(currentUser?.avatar_url)

  useEffect(() => {
    if (currentUser) {
      basicForm.setFieldsValue({
        full_name: currentUser.full_name,
        phone: currentUser.phone,
        email: currentUser.email,
        avatar_url: currentUser.avatar_url,
      })
      setPreviewUrl(currentUser.avatar_url)
    }
  }, [currentUser, basicForm])

  const handleBasicSubmit = async (values: Partial<Pick<User, 'full_name' | 'phone' | 'email' | 'avatar_url'>>) => {
    try {
      await updateMe(values).unwrap()
      message.success('基本信息更新成功')
      const result = await refetchMe()
      if (result.data) {
        dispatch(setUser(result.data))
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
    }
  }

  const handlePasswordSubmit = async (values: { old_password: string; new_password: string; confirm_new_password: string }) => {
    if (values.new_password !== values.confirm_new_password) {
      message.error('两次输入的新密码不一致')
      return
    }
    try {
      await changePassword({ old_password: values.old_password, new_password: values.new_password }).unwrap()
      message.success('密码修改成功')
      passwordForm.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '密码修改失败')
    }
  }

  const handleAvatarUpload = async (options: any) => {
    const { file, onSuccess, onError } = options
    try {
      const result = await uploadAvatar(file as File).unwrap()
      message.success('头像上传成功')
      basicForm.setFieldsValue({ avatar_url: result.file_url })
      setPreviewUrl(result.file_url)
      const refetched = await refetchMe()
      if (refetched.data) {
        dispatch(setUser(refetched.data))
      }
      onSuccess?.('ok')
    } catch (err: any) {
      message.error(err?.data?.detail || '头像上传失败')
      onError?.(err)
    }
  }

  const beforeUpload = (file: File) => {
    const isImage = file.type.startsWith('image/')
    if (!isImage) {
      message.error('只能上传图片文件')
    }
    const isLt2M = file.size / 1024 / 1024 < 2
    if (!isLt2M) {
      message.error('图片大小不能超过 2MB')
    }
    return isImage && isLt2M
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card title="基本信息">
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Avatar size={80} src={previewUrl}>
                {currentUser?.full_name?.charAt(0) || currentUser?.username?.charAt(0) || 'U'}
              </Avatar>
              <div style={{ marginTop: 12 }}>
                <Upload
                  customRequest={handleAvatarUpload}
                  beforeUpload={beforeUpload}
                  showUploadList={false}
                  accept="image/*"
                >
                  <Button icon={<UploadOutlined />} loading={uploadingAvatar}>
                    上传头像
                  </Button>
                </Upload>
              </div>
            </div>
            <Form form={basicForm} layout="vertical" onFinish={handleBasicSubmit}>
              <Form.Item name="avatar_url" hidden>
                <Input />
              </Form.Item>
              <Form.Item name="full_name" label="姓名">
                <Input />
              </Form.Item>
              <Form.Item name="phone" label="手机号">
                <Input />
              </Form.Item>
              <Form.Item name="email" label="邮箱" rules={[{ type: 'email' }]}>
                <Input />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={updating} block>
                  保存
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="修改密码">
            <Form form={passwordForm} layout="vertical" onFinish={handlePasswordSubmit}>
              <Form.Item
                name="old_password"
                label="旧密码"
                rules={[{ required: true, message: '请输入旧密码' }]}
              >
                <Input.Password />
              </Form.Item>
              <Form.Item
                name="new_password"
                label="新密码"
                rules={[
                  { required: true, message: '请输入新密码' },
                  {
                    pattern: passwordPattern,
                    message: '密码长度至少8位，且必须同时包含字母和数字',
                  },
                ]}
              >
                <Input.Password />
              </Form.Item>
              <Form.Item
                name="confirm_new_password"
                label="确认新密码"
                rules={[
                  { required: true, message: '请确认新密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('new_password') === value) {
                        return Promise.resolve()
                      }
                      return Promise.reject(new Error('两次输入的新密码不一致'))
                    },
                  }),
                ]}
              >
                <Input.Password />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={changing} block>
                  修改密码
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Profile
