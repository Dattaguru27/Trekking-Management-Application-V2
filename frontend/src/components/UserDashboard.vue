
<script setup>
import { ref, computed, onMounted } from 'vue'
const emit = defineEmits(['my-bookings', 'my-profile'])


const treks = ref([])
const searchText = ref('')
const difficultyFilter = ref('All')

const loading = ref(true)
const error = ref('')

const bookingTrekId = ref(null)
const bookingSuccess = ref('')

const exporting = ref(false)
const exportMessage = ref('')
const exportError = ref('')
const exportTaskId = ref(null)
const exportReady = ref(false)


const filteredTreks = computed(() => {
  const query = searchText.value.trim().toLowerCase()

  return treks.value.filter(trek => {
    const name = String(trek.name ?? '').toLowerCase()
    const location = String(trek.location ?? '').toLowerCase()

    const matchesSearch =
      name.includes(query) || location.includes(query)

    const matchesDifficulty =
      difficultyFilter.value === 'All' ||
      trek.difficulty === difficultyFilter.value

    return matchesSearch && matchesDifficulty
  })
})

async function loadTreks() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/user/treks', {
      credentials: 'same-origin'
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || 'Could not load available treks.'
      )
    }

    const result = Array.isArray(data)
      ? data
      : (data.treks ?? [])

    if (!Array.isArray(result)) {
      throw new Error('Unexpected trek response format.')
    }

    // Display only open treks with available places
    treks.value = result.filter(trek =>
      trek.status === 'Open' &&
      Number(trek.available_slots) > 0
    )

  } catch (err) {
    error.value = err.message
    treks.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadTreks)

async function downloadBookingHistory() {
  if (!exportTaskId.value || !exportReady.value) {
    return
  }

  try {
    exportError.value = ''

    const response = await fetch(
      `/api/user/bookings/export/${exportTaskId.value}/download`,
      {
        credentials: 'same-origin'
      }
    )

    if (!response.ok) {
      const data = await response.json()
      throw new Error(
        data.message || 'Could not download CSV.'
      )
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = 'booking_history.csv'

    document.body.appendChild(link)
    link.click()
    link.remove()

    window.URL.revokeObjectURL(url)

    exportMessage.value =
      'Booking history CSV downloaded successfully.'

  } catch (err) {
    exportError.value = err.message
  }
}

async function exportBookingHistory() {
  exporting.value = true
  exportMessage.value = ''
  exportError.value = ''
  exportTaskId.value = null
  exportReady.value = false

  try {
    const response = await fetch('/api/user/bookings/export', {
      method: 'POST',
      credentials: 'same-origin'
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || 'Could not start CSV export.'
      )
    }

    exportTaskId.value = data.task_id
exportReady.value = false

exportMessage.value =
  'CSV export started. Your booking history is being prepared.'

checkExportStatus(data.task_id)

  } catch (err) {
    exportError.value = err.message
  } finally {
    exporting.value = false
  }
}

async function checkExportStatus(taskId) {
  try {
    const response = await fetch(
      `/api/user/bookings/export/${taskId}/status`,
      {
        credentials: 'same-origin'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || 'Could not check export status.'
      )
    }

    if (data.status === 'SUCCESS') {
      exportReady.value = true
      exportMessage.value =
        'Your booking history CSV is ready to download.'
      return
    }

    if (data.status === 'FAILURE' || data.status === 'FAILED') {
      throw new Error('CSV export failed.')
    }

    exportMessage.value =
      'Preparing your booking history CSV...'

    // Check again after 2 seconds
    await new Promise(resolve => setTimeout(resolve, 2000))

    if (exportTaskId.value === taskId) {
      await checkExportStatus(taskId)
    }

  } catch (err) {
    exportError.value = err.message
    exportMessage.value = ''
  }
}

async function bookTrek(trek) {
  error.value = ''
  bookingSuccess.value = ''

  if (trek.status !== 'Open') {
    error.value = 'This trek is not open for booking.'
    return
  }

  if (Number(trek.available_slots) <= 0) {
    error.value = 'No slots available for this trek.'
    return
  }

  const confirmed = window.confirm(
    `Do you want to book "${trek.name}"?`
  )

  if (!confirmed) return

  bookingTrekId.value = trek.id

  try {
    const response = await fetch(
      `/api/user/treks/${trek.id}/book`,
      {
        method: 'POST',
        credentials: 'same-origin'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || 'Trek booking failed.'
      )
    }

    bookingSuccess.value =
      `You have successfully booked "${trek.name}"!`

    // Reload available treks and remaining slots
    await loadTreks()

  } catch (err) {
    error.value = err.message
  } finally {
    bookingTrekId.value = null
  }
}

</script>

<template>
  <div class="container my-5">

    <!-- Heading -->
    <div class="d-flex flex-wrap justify-content-between
                align-items-center gap-3 mb-4">
      <div>
        <h2 class="text-success fw-bold">
          Explore Treks
        </h2>
        <p class="text-muted mb-0">
          Find your next trekking adventure.
        </p>
      </div>

      
<div class="d-flex gap-2">
  <button
    class="btn btn-outline-success"
    @click="loadTreks"
    :disabled="loading"
  >
    Refresh
  </button>

  <button
    class="btn btn-success"
    @click="emit('my-bookings')"
  >
    My Bookings
  </button>

<button
  class="btn btn-outline-primary"
  type="button"
  :disabled="exporting"
  @click="exportBookingHistory"
>
  {{ exporting ? 'Starting Export...' : 'Export Booking History' }}
</button>


<button
  class="btn btn-outline-success"
  @click="emit('my-profile')"
>
  My Profile
</button>

</div>

    </div>

    <!-- Error Message -->
    <div
      v-if="error"
      class="alert alert-danger"
      role="alert"
    >
      {{ error }}
    </div>

<!-- Booking Success Message -->
<div
  v-if="bookingSuccess"
  class="alert alert-success"
  role="status"
>
  {{ bookingSuccess }}
</div>

<!-- CSV Export Message -->
<div
  v-if="exportMessage"
  class="alert alert-info"
  role="status"
>
  {{ exportMessage }}
</div>

<!-- Download CSV Button -->
<div v-if="exportReady" class="mb-3">
  <button
    type="button"
    class="btn btn-success"
    @click="downloadBookingHistory"
  >
    Download CSV
  </button>
</div>


<!-- CSV Export Error -->
<div
  v-if="exportError"
  class="alert alert-danger"
  role="alert"
>
  {{ exportError }}
</div>



    <!-- Search and Filters -->
    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h5 class="mb-3">Search Treks</h5>

        <div class="row g-3">
          <div class="col-md-8">
            <label for="trekSearch" class="form-label">
              Trek Name or Location
            </label>

            <input
              id="trekSearch"
              v-model="searchText"
              type="text"
              class="form-control"
              placeholder="Search by name or location..."
            />
          </div>

          <div class="col-md-4">
            <label for="difficulty" class="form-label">
              Difficulty
            </label>

            <select
              id="difficulty"
              v-model="difficultyFilter"
              class="form-select"
            >
              <option value="All">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Moderate">Moderate</option>
              <option value="Hard">Hard</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center my-5">
      <div
        class="spinner-border text-success"
        role="status"
      >
        <span class="visually-hidden">Loading...</span>
      </div>

      <p class="mt-3">Loading available treks...</p>
    </div>

    <!-- Trek Results -->
    <template v-else-if="!error">

      <div class="d-flex justify-content-between
                  align-items-center mb-3">
        <h4 class="mb-0">Available Treks</h4>

        <span class="badge bg-success">
          {{ filteredTreks.length }} Treks
        </span>
      </div>

      <div class="row g-4">
        <div
          v-for="trek in filteredTreks"
          :key="trek.id"
          class="col-md-6 col-lg-4"
        >
          <div class="card shadow-sm border-0 h-100">
            <div class="card-body">

              <div class="trek-icon mb-3">🏔️</div>

              <h5 class="card-title fw-bold">
                {{ trek.name }}
              </h5>

              <p class="text-muted mb-2">
                📍 {{ trek.location }}
              </p>

              <p class="mb-2">
                <strong>Difficulty:</strong>
                {{ trek.difficulty }}
              </p>

              <p class="mb-2">
                <strong>Duration:</strong>
                {{ trek.duration }}
              </p>

              <p class="mb-2">
                <strong>Available Slots:</strong>
                {{ trek.available_slots }}
              </p>

              <div class="mt-3">
                <span class="badge bg-success">
                  {{ trek.status }}
                </span>
              </div>

              
<!-- Book Trek Button -->
<button
  class="btn btn-success w-100 mt-3"
  type="button"
  :disabled="
    bookingTrekId !== null ||
    trek.status !== 'Open' ||
    Number(trek.available_slots) <= 0
  "
  @click="bookTrek(trek)"
>
  {{
    bookingTrekId === trek.id
      ? 'Booking...'
      : 'Book Trek'
  }}
</button>


            </div>
          </div>
        </div>

        <!-- No Treks -->
        <div
          v-if="filteredTreks.length === 0"
          class="col-12"
        >
          <div class="alert alert-info text-center">
            No available treks match your search.
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<style scoped>
.trek-icon {
  font-size: 40px;
}

.card {
  border-radius: 12px;
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-4px);
}
</style>
