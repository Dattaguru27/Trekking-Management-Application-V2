
<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['back'])

const staffList = ref([])
const treks = ref([])

const loading = ref(false)
const saving = ref(false)

const error = ref('')
const success = ref('')

const showAddForm = ref(false)
const selectedStaffId = ref('')
const selectedTrekId = ref('')

const form = ref({
  name: '',
  email: '',
  password: ''
})

async function readResponse(response) {
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Request failed.')
  }

  return data
}

async function loadData() {
  loading.value = true
  error.value = ''

  try {
    const [staffResponse, trekResponse] = await Promise.all([
      fetch('/api/admin/staff', {
        credentials: 'same-origin'
      }),
      fetch('/api/admin/treks', {
        credentials: 'same-origin'
      })
    ])

    const staffData = await readResponse(staffResponse)
    const trekData = await readResponse(trekResponse)

    staffList.value = Array.isArray(staffData)
      ? staffData
      : (staffData.staff ?? staffData.staff_members ?? [])

    treks.value = Array.isArray(trekData)
      ? trekData
      : (trekData.treks ?? [])

  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openAddForm() {
  form.value = {
    name: '',
    email: '',
    password: ''
  }

  error.value = ''
  success.value = ''
  showAddForm.value = true
}

async function createStaff() {
  error.value = ''
  success.value = ''

  if (
    !form.value.name.trim() ||
    !form.value.email.trim() ||
    !form.value.password
  ) {
    error.value = 'Please fill in all fields.'
    return
  }

  saving.value = true

  try {
    const response = await fetch('/api/admin/staff', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        name: form.value.name.trim(),
        email: form.value.email.trim(),
        password: form.value.password
      })
    })

    await readResponse(response)

    showAddForm.value = false
    success.value = 'Staff created successfully.'

    await loadData()

  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function assignStaff() {
  error.value = ''
  success.value = ''

  if (!selectedStaffId.value || !selectedTrekId.value) {
    error.value = 'Please select Staff and Trek.'
    return
  }

  const staff = staffList.value.find(
    item => item.id === Number(selectedStaffId.value)
  )

  if (!staff || staff.status !== 'approved') {
    error.value = 'Only approved Staff can be assigned.'
    return
  }

  saving.value = true

  try {
    const response = await fetch(
      `/api/admin/treks/${selectedTrekId.value}/assign-staff`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          staff_id: Number(selectedStaffId.value)
        })
      }
    )

    await readResponse(response)

    success.value = 'Staff assigned to trek successfully.'
    selectedStaffId.value = ''
    selectedTrekId.value = ''

    await loadData()

  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function changeStaffStatus(staff, action) {
  const message = action === 'blacklist'
    ? `Blacklist ${staff.name}?`
    : `Unblacklist ${staff.name}?`

  if (!window.confirm(message)) return

  error.value = ''
  success.value = ''

  saving.value = true

  try {
    const response = await fetch(
      `/api/admin/staff/${staff.id}/${action}`,
      {
        method: 'PUT',
        credentials: 'same-origin'
      }
    )

    await readResponse(response)

    success.value = action === 'blacklist'
      ? 'Staff blacklisted successfully.'
      : 'Staff unblacklisted successfully.'

    await loadData()

  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="container my-5">

    <!-- Heading -->
    <div class="d-flex flex-wrap justify-content-between
                align-items-center gap-3 mb-4">
      <div>
        <h2 class="text-success fw-bold">Manage Staff</h2>
        <p class="text-muted mb-0">
          Create, assign, and manage Staff accounts.
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
          @click="loadData"
          :disabled="loading"
        >
          Refresh
        </button>

        <button
          class="btn btn-success"
          @click="openAddForm"
        >
          + Add Staff
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-if="success" class="alert alert-success">
      {{ success }}
    </div>

    <!-- Add Staff Form -->
    <div v-if="showAddForm" class="card shadow-sm mb-4">
      <div class="card-body p-4">
        <h4 class="mb-3">Create New Staff</h4>

        <form @submit.prevent="createStaff">
          <div class="row g-3">

            <div class="col-md-4">
              <label class="form-label">Full Name</label>
              <input
                v-model="form.name"
                type="text"
                class="form-control"
                maxlength="100"
                required
              />
            </div>

            <div class="col-md-4">
              <label class="form-label">Email</label>
              <input
                v-model="form.email"
                type="email"
                class="form-control"
                maxlength="120"
                required
              />
            </div>

            <div class="col-md-4">
              <label class="form-label">Password</label>
              <input
                v-model="form.password"
                type="password"
                class="form-control"
                minlength="6"
                autocomplete="new-password"
                required
              />
            </div>

          </div>

          <div class="d-flex gap-2 mt-4">
            <button
              class="btn btn-success"
              type="submit"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : 'Create Staff' }}
            </button>

            <button
              class="btn btn-secondary"
              type="button"
              @click="showAddForm = false"
              :disabled="saving"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Assign Staff -->
    <div class="card shadow-sm mb-4">
      <div class="card-body p-4">
        <h4 class="mb-3">Assign Staff to Trek</h4>

        <form @submit.prevent="assignStaff">
          <div class="row g-3">

            <div class="col-md-5">
              <label class="form-label">Select Staff</label>
              <select
                v-model="selectedStaffId"
                class="form-select"
                required
              >
                <option value="">Choose Staff</option>

                <option
                  v-for="staff in staffList.filter(
                    s => s.status === 'approved'
                  )"
                  :key="staff.id"
                  :value="staff.id"
                >
                  {{ staff.name }} (ID: {{ staff.id }})
                </option>
              </select>
            </div>

            <div class="col-md-5">
              <label class="form-label">Select Trek</label>
              <select
                v-model="selectedTrekId"
                class="form-select"
                required
              >
                <option value="">Choose Trek</option>

                <option
                  v-for="trek in treks"
                  :key="trek.id"
                  :value="trek.id"
                >
                  {{ trek.name }} (ID: {{ trek.id }})
                </option>
              </select>
            </div>

            <div class="col-md-2 d-flex align-items-end">
              <button
                class="btn btn-success w-100"
                type="submit"
                :disabled="saving"
              >
                Assign
              </button>
            </div>

          </div>
        </form>
      </div>
    </div>

    <!-- Staff Table -->
    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-success"></div>
      <p class="mt-3">Loading Staff...</p>
    </div>

    <div v-else class="card shadow-sm">
      <div class="card-body">
        <h4 class="mb-3">Staff Members</h4>

        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="staff in staffList"
                :key="staff.id"
              >
                <td>{{ staff.id }}</td>
                <td>{{ staff.name }}</td>
                <td>{{ staff.email }}</td>

                <td>
                  <span
                    class="badge"
                    :class="staff.status === 'approved'
                      ? 'bg-success'
                      : 'bg-danger'"
                  >
                    {{ staff.status }}
                  </span>
                </td>

                <td>
                  <button
                    v-if="staff.status === 'approved'"
                    class="btn btn-sm btn-danger"
                    :disabled="saving"
                    @click="changeStaffStatus(staff, 'blacklist')"
                  >
                    Blacklist
                  </button>

                  <button
                    v-else-if="staff.status === 'blacklisted'"
                    class="btn btn-sm btn-success"
                    :disabled="saving"
                    @click="changeStaffStatus(staff, 'unblacklist')"
                  >
                    Unblacklist
                  </button>
                </td>
              </tr>

              <tr v-if="staffList.length === 0">
                <td colspan="5" class="text-center text-muted py-4">
                  No Staff members found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>
</template>
