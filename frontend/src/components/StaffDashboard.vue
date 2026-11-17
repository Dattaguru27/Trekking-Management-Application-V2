

<script setup>
import { ref, computed, onMounted } from 'vue'

const treks = ref([])
const loading = ref(true)
const savingId = ref(null)

const error = ref('')
const success = ref('')

const slotInputs = ref({})
const statusInputs = ref({})

const selectedTrek = ref(null)
const participants = ref([])
const loadingParticipants = ref(false)
const participantError = ref('')


const totalTreks = computed(() => treks.value.length)

const openTreks = computed(() =>
  treks.value.filter(trek => trek.status === 'Open').length
)

async function readResponse(response) {
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Request failed.')
  }

  return data
}

async function loadDashboard() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/staff/dashboard', {
      credentials: 'same-origin'
    })

    const data = await readResponse(response)

    const result = Array.isArray(data)
      ? data
      : (data.assigned_treks ?? data.treks ?? [])

    if (!Array.isArray(result)) {
      throw new Error('Unexpected dashboard response.')
    }

    treks.value = result

    // Set initial values for each trek's controls
    slotInputs.value = {}
    statusInputs.value = {}

    for (const trek of result) {
      slotInputs.value[trek.id] = trek.available_slots
      statusInputs.value[trek.id] = trek.status
    }

  } catch (err) {
    error.value = err.message
    treks.value = []
  } finally {
    loading.value = false
  }
}

async function updateSlots(trek) {
  error.value = ''
  success.value = ''

  const slots = Number(slotInputs.value[trek.id])

  if (
    !Number.isInteger(slots) ||
    slots < 0 ||
    slotInputs.value[trek.id] === ''
  ) {
    error.value = 'Slots must be a non-negative whole number.'
    return
  }

  savingId.value = trek.id

  try {
    const response = await fetch(
      `/api/staff/treks/${trek.id}/slots`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          available_slots: slots
        })
      }
    )

    await readResponse(response)

    await loadDashboard()
    success.value = 'Available slots updated successfully.'

  } catch (err) {
    error.value = err.message
  } finally {
    savingId.value = null
  }
}

async function updateStatus(trek) {
  error.value = ''
  success.value = ''

  const status = statusInputs.value[trek.id]

  if (!['Open', 'Closed', 'Completed'].includes(status)) {
    error.value = 'Invalid trek status.'
    return
  }

  savingId.value = trek.id

  try {
    const response = await fetch(
      `/api/staff/treks/${trek.id}/status`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          status: status
        })
      }
    )

    await readResponse(response)

    await loadDashboard()
    success.value = 'Trek status updated successfully.'

  } catch (err) {
    error.value = err.message
  } finally {
    savingId.value = null
  }
}


async function viewParticipants(trek) {
  selectedTrek.value = trek
  participants.value = []
  participantError.value = ''
  loadingParticipants.value = true

  try {
    const response = await fetch(
      `/api/staff/treks/${trek.id}/participants`,
      {
        credentials: 'same-origin'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || 'Could not load participants.'
      )
    }

    const result = Array.isArray(data)
      ? data
      : (data.participants ?? [])

    if (!Array.isArray(result)) {
      throw new Error('Unexpected participants response.')
    }

    participants.value = result

  } catch (err) {
    participantError.value = err.message
  } finally {
    loadingParticipants.value = false
  }
}

function closeParticipants() {
  selectedTrek.value = null
  participants.value = []
  participantError.value = ''
}

onMounted(loadDashboard)
</script>


<template>
  <div class="container my-5">

    <!-- Heading -->
    <div class="d-flex flex-wrap justify-content-between
                align-items-center gap-3 mb-4">
      <div>
        <h2 class="text-success fw-bold">
          Staff Dashboard
        </h2>
        <p class="text-muted mb-0">
          View and monitor your assigned treks.
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

    <!-- Error -->
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

<!-- Success Message -->
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
      <p class="mt-3">Loading assigned treks...</p>
    </div>

    <template v-else-if="!error">

      <!-- Statistics -->
      <div class="row g-4 mb-4">

        <div class="col-md-6">
          <div class="card shadow-sm border-0 h-100">
            <div class="card-body text-center">
              <div class="stat-icon">🏔️</div>
              <h2 class="fw-bold text-primary">
                {{ totalTreks }}
              </h2>
              <p class="text-muted mb-0">
                Assigned Treks
              </p>
            </div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="card shadow-sm border-0 h-100">
            <div class="card-body text-center">
              <div class="stat-icon">✅</div>
              <h2 class="fw-bold text-success">
                {{ openTreks }}
              </h2>
              <p class="text-muted mb-0">
                Open Treks
              </p>
            </div>
          </div>
        </div>

      </div>

      <!-- Assigned Treks -->
      <div class="card shadow-sm">
        <div class="card-body">

          <h4 class="mb-3">My Assigned Treks</h4>

          <div class="table-responsive">
            <table class="table table-hover align-middle">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Trek Name</th>
                  <th>Location</th>
                  <th>Difficulty</th>
                  <th>Duration</th>
                  <th>Available Slots</th>
<th>Update Slots</th>
<th>Status</th>
<th>Update Status</th>
<th>Participants</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="trek in treks"
                  :key="trek.id"
                >
                  <td>{{ trek.id }}</td>
                  <td>{{ trek.name }}</td>
                  <td>{{ trek.location }}</td>
                  <td>{{ trek.difficulty }}</td>
                  <td>{{ trek.duration }}</td>
                  <td>{{ trek.available_slots }}</td>

<!-- Update Slots -->
<td>
  <div class="d-flex gap-2" style="min-width: 170px;">
    <input
      v-model.number="slotInputs[trek.id]"
      type="number"
      min="0"
      step="1"
      class="form-control form-control-sm"
      aria-label="Available slots"
    />

    <button
      class="btn btn-sm btn-success"
      :disabled="savingId !== null || loading"
      @click="updateSlots(trek)"
    >
      Save
    </button>
  </div>
</td>


                  <td>
                    <span
                      class="badge"
                      :class="{
                        'bg-success': trek.status === 'Open',
                        'bg-warning text-dark': trek.status === 'Closed',
                        'bg-secondary': trek.status === 'Completed'
                      }"
                    >
                      {{ trek.status }}
                    </span>
                  </td>

<!-- Update Status -->
<td>
  <div class="d-flex gap-2" style="min-width: 210px;">
    <select
      v-model="statusInputs[trek.id]"
      class="form-select form-select-sm"
      aria-label="Trek status"
    >
      <option value="Open">Open</option>
      <option value="Closed">Closed</option>
      <option value="Completed">Completed</option>
    </select>

    <button
      class="btn btn-sm btn-success"
      :disabled="savingId !== null || loading"
      @click="updateStatus(trek)"
    >
      Save
    </button>
  </div>
</td>

<!-- View Participants -->
<td>
  <button
    class="btn btn-sm btn-outline-primary"
    @click="viewParticipants(trek)"
  >
    View Participants
  </button>
</td>


                </tr>

                <tr v-if="treks.length === 0">
                  <td
                    colspan="10"
                    class="text-center text-muted py-4"
                  >
                    No treks assigned to you yet.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

        </div>
      </div>

<!-- Participants Section -->
<div
  v-if="selectedTrek"
  class="card shadow-sm mt-4"
>
  <div class="card-body">

    <div class="d-flex justify-content-between
                align-items-center mb-3">
      <div>
        <h4 class="mb-1">Trek Participants</h4>
        <p class="text-muted mb-0">
          {{ selectedTrek.name }}
        </p>
      </div>

      <button
        class="btn btn-outline-secondary"
        @click="closeParticipants"
      >
        Close
      </button>
    </div>

    <div
      v-if="participantError"
      class="alert alert-danger"
    >
      {{ participantError }}
    </div>

    <div
      v-if="loadingParticipants"
      class="text-center my-4"
    >
      <div class="spinner-border text-success"></div>
      <p class="mt-2">Loading participants...</p>
    </div>

    <div v-else-if="!participantError">
      <p class="fw-semibold">
        Total Participants: {{ participants.length }}
      </p>

      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Booking ID</th>
              <th>Booking Status</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(participant, index) in participants"
              :key="participant.booking_id ?? index"
            >
              <td>
                {{ participant.user_id ?? participant.id ?? '-' }}
              </td>

              <td>
                {{ participant.name ?? participant.user_name ?? '-' }}
              </td>

              <td>
                {{ participant.email ?? '-' }}
              </td>

              <td>
                {{ participant.booking_id ?? '-' }}
              </td>

              <td>
                <span class="badge bg-success">
                  {{ participant.booking_status ??
                     participant.status ?? 'Booked' }}
                </span>
              </td>
            </tr>

            <tr v-if="participants.length === 0">
              <td
                colspan="5"
                class="text-center text-muted py-4"
              >
                No participants yet.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</div>


    </template>

  </div>
</template>

<style scoped>
.stat-icon {
  font-size: 35px;
  margin-bottom: 10px;
}

.card {
  border-radius: 12px;
}
</style>
