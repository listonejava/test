<template>
  <div class="user-list">
    <table>
      <tr v-for="user in users" :key="user.id">
        <td>{{ user.name }}</td>
        <td>{{ user.email }}</td>
        <td><button @click="deleteUser(user.id)">删除</button></td>
      </tr>
    </table>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UserList',
  data() {
    return {
      users: []
    }
  },
  mounted() {
    this.loadUsers()
  },
  methods: {
    loadUsers() {
      axios.get('/api/user/list').then(res => {
        this.users = res.data
      })
    },
    deleteUser(id) {
      axios.delete(`/api/user/${id}`).then(() => {
        this.loadUsers()
      })
    }
  }
}
</script>
