
<script setup>
import { ref, computed, onMounted } from 'vue'

const emit = defineEmits(['back'])

const bookings = ref([])
const loading = ref(true)
const cancellingId = ref(null)

const error = ref('')
const success = ref('')

const totalBookings = computed(() => bookings.value.length)


const activeBookings = computed(() =>
  bookings.value.filter(
    booking => booking.booking_status === 'Booked'
  ).length
)


async function readResponse(response) {
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Request failed.')
  }

  return data
}

async function loadBookings() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/user/bookings', {
      credentials: 'same-origin'
    })

    const data = await readResponse(response)

    const result = Array.isArray(data)
      ? data
      : (data.bookings ?? [])

    if (!Array.isArray(result)) {
      throw new Error('Unexpected bookings response format.')
    }

    bookings.value = result

  } catch (err) {
    error.value = err.message
    bookings.value = []
  } finally {
    loading.value = false
  }
}


async function cancelBooking(booking) {
  if (booking.booking_status !== 'Booked') return

  const confirmed = window.confirm(
    `Are you sure you want to cancel booking #${booking.booking_id}?`
  )

  if (!confirmed) return

  cancellingId.value = booking.booking_id
  error.value = ''
  success.value = ''

  try {
    const response = await fetch(
      `/api/user/bookings/${booking.booking_id}/cancel`,
      {
        method: 'PUT',
        credentials: 'same-origin'
      }
    )

    await readResponse(response)

    await loadBookings()

    success.value = 'Booking cancelled successfully.'

  } catch (err) {
    error.value = err.message
  } finally {
    cancellingId.value = null
  }
}


function formatDate(value) {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

onMounted(loadBookings)
</script>

<template>
  <div class="container my-5">

    <!-- Heading -->
    <div class="d-flex flex-wrap justify-content-between
                align-items-center gap-3 mb-4">
      <div>
        <h2 class="text-success fw-bold">My Bookings</h2>
        <p class="text-muted mb-0">
          View your booking history and manage reservations.
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
          @click="loadBookings"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="alert alert-danger"
      role="alert"
    >
      {{ error }}
    </div>

    <!-- Success -->
    <div
      v-if="success"
      class="alert alert-success"
      role="status"
    >
      {{ success }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-success"></div>
      <p class="mt-3">Loading your bookings...</p>
    </div>

    <template v-else-if="!error">

      <!-- Statistics -->
      <div class="row g-4 mb-4">

        <div class="col-md-6">
          <div class="card shadow-sm border-0">
            <div class="card-body text-center">
              <h2 class="fw-bold text-primary">
                {{ totalBookings }}
              </h2>
              <p class="text-muted mb-0">
                Total Bookings
              </p>
            </div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="card shadow-sm border-0">
            <div class="card-body text-center">
              <h2 class="fw-bold text-success">
                {{ activeBookings }}
              </h2>
              <p class="text-muted mb-0">
                Active Bookings
              </p>
            </div>
          </div>
        </div>

      </div>

      <!-- Bookings Table -->
      <div class="card shadow-sm">
        <div class="card-body">

          <h4 class="mb-3">Booking History</h4>

          <div class="table-responsive">
            <table class="table table-hover align-middle">
              <thead>
                <tr>
                  <th>Booking ID</th>
                  <th>Trek Name</th>
                  <th>Location</th>
                  <th>Booking Date</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              
<tbody>
  <tr
    v-for="booking in bookings"
    :key="booking.booking_id"
  >
    <!-- Booking ID -->
    <td>{{ booking.booking_id }}</td>

    <!-- Trek Name -->
    <td>{{ booking.trek_name }}</td>

    <!-- Location -->
    <td>{{ booking.location ?? '-' }}</td>

    <!-- Booking Date -->
    <td>{{ formatDate(booking.booking_date) }}</td>

    <!-- Booking Status -->
    <td>
      <span
        class="badge"
        :class="{
          'bg-success':
            booking.booking_status === 'Booked',
          'bg-secondary':
            booking.booking_status === 'Cancelled',
          'bg-warning text-dark':
            !['Booked', 'Cancelled'].includes(
              booking.booking_status
            )
        }"
      >
        {{ booking.booking_status }}
      </span>
    </td>

    <!-- Actions -->
    <td>
      <button
        v-if="booking.booking_status === 'Booked'"
        class="btn btn-sm btn-danger"
        :disabled="cancellingId !== null"
        @click="cancelBooking(booking)"
      >
        {{
          cancellingId === booking.booking_id
            ? 'Cancelling...'
            : 'Cancel Booking'
        }}
      </button>

      <span v-else class="text-muted">
        —
      </span>
    </td>
  </tr>

  <tr v-if="bookings.length === 0">
    <td
      colspan="6"
      class="text-center text-muted py-4"
    >
      You have not booked any treks yet.
    </td>
  </tr>
</tbody>

            </table>
          </div>

        </div>
      </div>

    </template>

  </div>
</template>

<style scoped>
.card {
  border-radius: 12px;
}
</style>
