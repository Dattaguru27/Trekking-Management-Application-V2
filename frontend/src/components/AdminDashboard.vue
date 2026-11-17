
<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits([
  'manage-treks',
  'manage-staff',
  'manage-users',
  'view-bookings'
])

const totalUsers = ref(0)
const totalStaff = ref(0)
const totalTreks = ref(0)
const totalBookings = ref(0)

const loading = ref(true)
const error = ref('')

async function loadDashboard() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/admin/dashboard', {
      credentials: 'same-origin'
    })

    const data = await response.json()

    if (!response.ok) {
      error.value = data.message || 'Failed to load dashboard.'
      return
    }

    totalUsers.value = data.total_users ?? 0
    totalStaff.value = data.total_staff ?? 0
    totalTreks.value = data.total_treks ?? 0
    totalBookings.value = data.total_bookings ?? 0

  } catch (err) {
    error.value = 'Cannot connect to the Flask server.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="container my-5">

    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="text-success fw-bold">
          Admin Dashboard
        </h2>
        <p class="text-muted mb-0">
          Trekking Management Overview
        </p>
      </div>

      <button
        class="btn btn-outline-success"
        @click="loadDashboard"
        :disabled="loading"
      >
        Refresh
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-success"></div>
      <p class="mt-3">Loading dashboard...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Dashboard Statistics -->
    <div v-else class="row g-4">

      <!-- Users -->
      <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm border-0 h-100">
          <div class="card-body text-center">
            <div class="stat-icon">👥</div>
            <h2 class="fw-bold text-primary">
              {{ totalUsers }}
            </h2>
            <p class="text-muted mb-0">
              Total Users
            </p>
          </div>
        </div>
      </div>

      <!-- Staff -->
      <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm border-0 h-100">
          <div class="card-body text-center">
            <div class="stat-icon">🧑‍💼</div>
            <h2 class="fw-bold text-success">
              {{ totalStaff }}
            </h2>
            <p class="text-muted mb-0">
              Total Staff
            </p>
          </div>
        </div>
      </div>

      <!-- Treks -->
      <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm border-0 h-100">
          <div class="card-body text-center">
            <div class="stat-icon">🏔️</div>
            <h2 class="fw-bold text-warning">
              {{ totalTreks }}
            </h2>
            <p class="text-muted mb-0">
              Total Treks
            </p>
          </div>
        </div>
      </div>

      <!-- Bookings -->
      <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm border-0 h-100">
          <div class="card-body text-center">
            <div class="stat-icon">📅</div>
            <h2 class="fw-bold text-danger">
              {{ totalBookings }}
            </h2>
            <p class="text-muted mb-0">
              Total Bookings
            </p>
          </div>
        </div>
      </div>

    </div>

    <!-- Admin Features -->
    <div class="mt-5">
      <h4 class="fw-bold mb-3">
        Admin Management
      </h4>

      <div class="row g-3">

        <div class="col-md-4">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5>🏔️ Manage Treks</h5>
              <p class="text-muted">
                Add, edit, and manage trekking events.
              </p>
              <span class="badge bg-secondary">
                 
<button
  class="btn btn-success"
  @click="emit('manage-treks')"
>
  Manage Treks
</button>

              </span>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5>🧑‍💼 Manage Staff</h5>
              <p class="text-muted">
                Create Staff and assign them to treks.
              </p>
              <span class="badge bg-secondary">
                
<button
  class="btn btn-success"
  @click="emit('manage-staff')"
>
  Manage Staff
</button>

              </span>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5>👥 Manage Users</h5>
              <p class="text-muted">
                View Users and manage their accounts.
              </p>
              <span class="badge bg-secondary">
                
<button
  class="btn btn-success"
  @click="emit('manage-users')"
>
  Manage Users
</button>

              </span>
            </div>

          </div>
          
        </div>
<!-- View All Bookings -->
<div class="col-md-4">
  <div class="card shadow-sm h-100">
    <div class="card-body">
      <h5>📅 View All Bookings</h5>
      <p class="text-muted">
        View all user bookings and their status.
      </p>

      <button
        class="btn btn-success"
        @click="emit('view-bookings')"
      >
        View All Bookings
      </button>
    </div>
  </div>
</div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.stat-icon {
  font-size: 35px;
  margin-bottom: 10px;
}

.card {
  border-radius: 12px;
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-4px);
}
</style>
