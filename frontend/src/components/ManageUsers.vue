
<script setup>
import { ref, computed, onMounted } from 'vue'

const emit = defineEmits(['back'])

const users = ref([])
const searchText = ref('')
const searchType = ref('name')

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')

async function readResponse(response) {
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Request failed.')
  }

  return data
}

// Load all registered Trekkers
async function loadUsers() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/admin/users', {
      credentials: 'same-origin'
    })

    const data = await readResponse(response)

    const result = Array.isArray(data)
      ? data
      : (data.users ?? [])

    users.value = result.filter(
      user => user.role === 'user'
    )

  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// Filter by name or ID
const filteredUsers = computed(() => {
  const query = searchText.value.trim().toLowerCase()

  if (!query) {
    return users.value
  }

  if (searchType.value === 'id') {
    return users.value.filter(
      user => String(user.id) === query
    )
  }

  return users.value.filter(
    user => user.name.toLowerCase().includes(query)
  )
})

// Blacklist or Unblacklist a User
async function changeUserStatus(user, action) {
  const message = action === 'blacklist'
    ? `Are you sure you want to blacklist ${user.name}?`
    : `Are you sure you want to unblacklist ${user.name}?`

  if (!window.confirm(message)) {
    return
  }

  saving.value = true
  error.value = ''
  success.value = ''

  try {
    const response = await fetch(
      `/api/admin/users/${user.id}/${action}`,
      {
        method: 'PUT',
        credentials: 'same-origin'
      }
    )

    await readResponse(response)

    success.value = action === 'blacklist'
      ? 'User blacklisted successfully.'
      : 'User unblacklisted successfully.'

    await loadUsers()

  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

onMounted(loadUsers)
</script>

<template>
  <div class="container my-5">

    <!-- Heading -->
    <div class="d-flex flex-wrap justify-content-between
                align-items-center gap-3 mb-4">

      <div>
        <h2 class="text-success fw-bold">
          Manage Users
        </h2>

        <p class="text-muted mb-0">
          View, search, blacklist, and unblacklist Trekkers.
        </p>
      </div>

      <div class="d-flex gap-2">
        <button
          class="btn btn-outline-secondary"
          @click="emit('back')"
        >
          Back
        </button>

        <button
          class="btn btn-outline-success"
          @click="loadUsers"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>

    </div>

    <!-- Error Message -->
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Success Message -->
    <div v-if="success" class="alert alert-success">
      {{ success }}
    </div>

    <!-- Search Section -->
    <div class="card shadow-sm mb-4">
      <div class="card-body">

        <h5 class="mb-3">Search Users</h5>

        <div class="row g-3">

          <div class="col-md-4">
            <select
              v-model="searchType"
              class="form-select"
            >
              <option value="name">
                Search by Name
              </option>

              <option value="id">
                Search by ID
              </option>
            </select>
          </div>

          <div class="col-md-8">
            <input
              v-model="searchText"
              :type="searchType === 'id' ? 'number' : 'text'"
              class="form-control"
              :placeholder="searchType === 'id'
                ? 'Enter User ID'
                : 'Enter User Name'"
              min="1"
            />
          </div>

        </div>
      </div>
    </div>

    <!-- Users Table -->
    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-success"></div>
      <p class="mt-3">Loading Users...</p>
    </div>

    <div v-else class="card shadow-sm">
      <div class="card-body">

        <div class="d-flex justify-content-between
                    align-items-center mb-3">
          <h4 class="mb-0">Registered Trekkers</h4>

          <span class="badge bg-success">
            {{ filteredUsers.length }} Users
          </span>
        </div>

        <div class="table-responsive">
          <table class="table table-hover align-middle">

            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="user in filteredUsers"
                :key="user.id"
              >
                <td>{{ user.id }}</td>
                <td>{{ user.name }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.role }}</td>

                <td>
                  <span
                    class="badge"
                    :class="user.status === 'approved'
                      ? 'bg-success'
                      : user.status === 'blacklisted'
                        ? 'bg-danger'
                        : 'bg-warning text-dark'"
                  >
                    {{ user.status }}
                  </span>
                </td>

                <td>
                  <button
                    v-if="user.status === 'approved'"
                    class="btn btn-sm btn-danger"
                    :disabled="saving"
                    @click="changeUserStatus(user, 'blacklist')"
                  >
                    Blacklist
                  </button>

                  <button
                    v-else-if="user.status === 'blacklisted'"
                    class="btn btn-sm btn-success"
                    :disabled="saving"
                    @click="changeUserStatus(user, 'unblacklist')"
                  >
                    Unblacklist
                  </button>
                </td>
              </tr>

              <tr v-if="filteredUsers.length === 0">
                <td
                  colspan="6"
                  class="text-center text-muted py-4"
                >
                  No Users found.
                </td>
              </tr>
            </tbody>

          </table>
        </div>
      </div>
    </div>

  </div>
</template>
