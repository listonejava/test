<template>
  <div class="order-list">
    <h2>Order Management</h2>
    <button @click="loadOrders">Refresh</button>
    
    <table>
      <thead>
        <tr>
          <th>Order No</th>
          <th>User ID</th>
          <th>Amount</th>
          <th>Status</th>
          <th>Created At</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="order in orders" :key="order.id">
          <td>{{ order.orderNo }}</td>
          <td>{{ order.userId }}</td>
          <td>{{ order.totalAmount }}</td>
          <td>{{ order.status }}</td>
          <td>{{ order.createdAt }}</td>
          <td>
            <button @click="viewOrder(order)">View</button>
            <button @click="deleteOrder(order.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getOrderList, deleteOrder } from '../api/orderApi'

const orders = ref([])

const loadOrders = async () => {
  const result = await getOrderList()
  orders.value = result.data
}

const viewOrder = (order) => {
  console.log('View order:', order)
}

const deleteOrder = async (id) => {
  if (confirm('Are you sure to delete this order?')) {
    await deleteOrder(id)
    loadOrders()
  }
}

onMounted(() => {
  loadOrders()
})
</script>
