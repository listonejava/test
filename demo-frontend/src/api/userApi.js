import axios from 'axios'

const API_BASE = '/api/user'

export const getUserList = () => {
  return axios.get(`${API_BASE}/list`)
}

export const getUserById = (id) => {
  return axios.get(`${API_BASE}/${id}`)
}

export const createUser = (data) => {
  return axios.post(API_BASE, data)
}

export const updateUser = (id, data) => {
  return axios.put(`${API_BASE}/${id}`, data)
}

export const deleteUser = (id) => {
  return axios.delete(`${API_BASE}/${id}`)
}

export const getUserByUsername = (username) => {
  return axios.get(`${API_BASE}/username/${username}`)
}
