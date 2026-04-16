<template>
  <div class="user-list">
    <h2>User Management</h2>
    <button @click="loadUsers">Refresh</button>
    <button @click="showCreateForm = true">Add User</button>
    
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Email</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>
            <button @click="editUser(user)">Edit</button>
            <button @click="deleteUser(user.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getUserList, deleteUser } from '../api/userApi'

const users = ref([])
const showCreateForm = ref(false)

const loadUsers = async () => {
  const result = await getUserList()
  users.value = result.data
}

const editUser = (user) => {
  console.log('Edit user:', user)
}

const deleteUser = async (id) => {
  if (confirm('Are you sure?')) {
    await deleteUser(id)
    loadUsers()
  }
}

onMounted(() => {
  loadUsers()
})
</script>
