
<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['back'])

const treks = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const slotInputs = ref({})

const showForm = ref(false)
const editingId = ref(null)


const emptyForm = () => ({
  name: '',
  location: '',
  difficulty: 'Easy',
  duration: '',
  available_slots: 0,
  status: 'Open',
  start_date: '',
  instructions: ''
})


const form = ref(emptyForm())

async function loadTreks() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/admin/treks', {
      credentials: 'same-origin'
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Could not load treks.')
    }

    // Supports a list or an object containing a treks list
    treks.value = Array.isArray(data)
      ? data
      : (data.treks ?? [])

  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openAddForm() {
  editingId.value = null
  form.value = emptyForm()
  showForm.value = true
  error.value = ''
  success.value = ''
}


function openEditForm(trek) {
  editingId.value = trek.id

  form.value = {
    name: trek.name,
    location: trek.location,
    difficulty: trek.difficulty,
    duration: trek.duration,
    available_slots: trek.available_slots,
    status: trek.status,
    start_date: trek.start_date ?? '',
    instructions: trek.instructions ?? ''
  }

  showForm.value = true
  error.value = ''
  success.value = ''
}


function closeForm() {
  showForm.value = false
  editingId.value = null
  form.value = emptyForm()
}

async function saveTrek() {
  error.value = ''
  success.value = ''

  const slots = Number(form.value.available_slots)

  if (
    !Number.isInteger(slots) ||
    slots < 0
  ) {
    error.value = 'Slots must be a non-negative whole number.'
    return
  }

  if (
    !form.value.name.trim() ||
    !form.value.location.trim() ||
    !form.value.duration.trim()
  ) {
    error.value = 'Please fill in all required fields.'
    return
  }

  saving.value = true

  const isEditing = editingId.value !== null

  const url = isEditing
    ? `/api/admin/treks/${editingId.value}`
    : '/api/admin/treks'

  const method = isEditing ? 'PUT' : 'POST'

  
const payload = {
  name: form.value.name.trim(),
  location: form.value.location.trim(),
  difficulty: form.value.difficulty,
  duration: form.value.duration.trim(),
  available_slots: slots,
  status: form.value.status,
  start_date: form.value.start_date || null,
  instructions: form.value.instructions.trim()
}


  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      body: JSON.stringify(payload)
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Could not save trek.')
    }

    closeForm()

    success.value = isEditing
      ? 'Trek updated successfully.'
      : 'Trek added successfully.'

    await loadTreks()

  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function deleteTrek(trek) {
  const confirmed = window.confirm(
    `Are you sure you want to delete "${trek.name}"?`
  )

  if (!confirmed) return

  error.value = ''
  success.value = ''

  try {
    const response = await fetch(
      `/api/admin/treks/${trek.id}`,
      {
        method: 'DELETE',
        credentials: 'same-origin'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'Could not delete trek.')
    }

    success.value = 'Trek deleted successfully.'
    await loadTreks()

  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadTreks)
</script>

<template>
  <div class="container my-5">

    <div class="d-flex flex-wrap justify-content-between
                align-items-center gap-3 mb-4">
      <div>
        <h2 class="text-success fw-bold">Manage Treks</h2>
        <p class="text-muted mb-0">
          Add, edit, view, and delete trekking events.
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
          @click="loadTreks"
          :disabled="loading"
        >
          Refresh
        </button>

        <button
          class="btn btn-success"
          @click="openAddForm"
        >
          + Add Trek
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-if="success" class="alert alert-success">
      {{ success }}
    </div>

    <!-- Add / Edit Form -->
    <div v-if="showForm" class="card shadow-sm mb-4">
      <div class="card-body p-4">
        <h4 class="mb-4">
          {{ editingId === null ? 'Add New Trek' : 'Edit Trek' }}
        </h4>

        <form @submit.prevent="saveTrek">
          <div class="row g-3">

            <div class="col-md-6">
              <label class="form-label">Trek Name</label>
              <input
                v-model="form.name"
                class="form-control"
                maxlength="100"
                required
              />
            </div>

            <div class="col-md-6">
              <label class="form-label">Location</label>
              <input
                v-model="form.location"
                class="form-control"
                maxlength="100"
                required
              />
            </div>

            <div class="col-md-6">
              <label class="form-label">Difficulty</label>
              <select
                v-model="form.difficulty"
                class="form-select"
                required
              >
                <option>Easy</option>
                <option>Moderate</option>
                <option>Hard</option>
              </select>
            </div>

            <div class="col-md-6">
              <label class="form-label">Duration</label>
              <input
                v-model="form.duration"
                class="form-control"
                placeholder="e.g. 2 Days"
                maxlength="50"
                required
              />
            </div>

            <div class="col-md-6">
              <label class="form-label">Available Slots</label>
              <input
                v-model.number="form.available_slots"
                type="number"
                min="0"
                step="1"
                class="form-control"
                required
              />
            </div>

            <div class="col-md-6">
              <label class="form-label">Status</label>
              <select v-model="form.status" class="form-select">
                <option>Open</option>
                <option>Closed</option>
                <option>Completed</option>
              </select>
            </div>

<!-- Trek Start Date -->
<div class="col-md-6">
  <label class="form-label">Start Date</label>
  <input
    v-model="form.start_date"
    type="date"
    class="form-control"
  />
</div>

<!-- Trek Instructions -->
<div class="col-12">
  <label class="form-label">Instructions</label>
  <textarea
    v-model="form.instructions"
    class="form-control"
    rows="3"
    placeholder="e.g. Bring water, trekking shoes and an ID card."
  ></textarea>
</div>


          </div>

          <div class="d-flex gap-2 mt-4">
            <button
              type="submit"
              class="btn btn-success"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : 'Save Trek' }}
            </button>

            <button
              type="button"
              class="btn btn-secondary"
              @click="closeForm"
              :disabled="saving"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Trek Table -->
    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-success"></div>
      <p class="mt-3">Loading treks...</p>
    </div>

    <div v-else class="card shadow-sm">
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th>ID</th>
                <th>Trek Name</th>
                <th>Location</th>
                <th>Difficulty</th>
                <th>Duration</th>
                <th>Slots</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="trek in treks" :key="trek.id">
                <td>{{ trek.id }}</td>
                <td>{{ trek.name }}</td>
                <td>{{ trek.location }}</td>
                <td>{{ trek.difficulty }}</td>
                <td>{{ trek.duration }}</td>
                <td>{{ trek.available_slots }}</td>



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

                <td>
                  <div class="d-flex gap-2">
                    <button
                      class="btn btn-sm btn-primary"
                      @click="openEditForm(trek)"
                    >
                      Edit
                    </button>

                    <button
                      class="btn btn-sm btn-danger"
                      @click="deleteTrek(trek)"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>

              <tr v-if="treks.length === 0">
                <td colspan="8" class="text-center text-muted py-4">
                  No treks found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>
</template>
