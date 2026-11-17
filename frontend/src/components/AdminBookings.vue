
<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['back'])

const bookings = ref([])
const loading = ref(false)
const error = ref('')

async function loadBookings() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/admin/bookings', {
      credentials: 'same-origin'
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Could not load bookings.')
    }

    bookings.value = data.bookings ?? []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(loadBookings)
</script>

<template>
  <div class="container my-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="text-success fw-bold">All Bookings</h2>
        <p class="text-muted mb-0">
          View all user bookings and trekking history.
        </p>
      </div>

      <div class="d-flex gap-2">
        <button class="btn btn-outline-secondary" @click="emit('back')">
          Back
        </button>

        <button
          class="btn btn-outline-success"
          @click="loadBookings"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-success"></div>
      <p class="mt-3">Loading bookings...</p>
    </div>

    <div v-else class="card shadow-sm">
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th>Booking ID</th>
                <th>User</th>
                <th>Trek</th>
                <th>Location</th>
                <th>Booking Date</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="booking in bookings" :key="booking.id">
                <td>{{ booking.id }}</td>
                <td>{{ booking.user_name }}</td>
                <td>{{ booking.trek_name }}</td>
                <td>{{ booking.location }}</td>
                <td>{{ booking.booking_date }}</td>
                <td>
                  <span
                    class="badge"
                    :class="{
                      'bg-success': booking.status === 'Booked',
                      'bg-danger': booking.status === 'Cancelled',
                      'bg-secondary': booking.status === 'Completed'
                    }"
                  >
                    {{ booking.status }}
                  </span>
                </td>
              </tr>

              <tr v-if="bookings.length === 0">
                <td colspan="6" class="text-center text-muted py-4">
                  No bookings found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
