import axios from 'axios'

const API_BASE = '/api/order'

export const getOrderList = () => {
  return axios.get(`${API_BASE}/list`)
}

export const getOrderById = (id) => {
  return axios.get(`${API_BASE}/${id}`)
}

export const getOrdersByUserId = (userId) => {
  return axios.get(`${API_BASE}/user/${userId}`)
}

export const createOrder = (data) => {
  return axios.post(API_BASE, data)
}

export const updateOrder = (id, data) => {
  return axios.put(`${API_BASE}/${id}`, data)
}

export const deleteOrder = (id) => {
  return axios.delete(`${API_BASE}/${id}`)
}
