
<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['back'])

const profile = ref({
  id: null,
  name: '',
  email: '',
  role: '',
  status: ''
})

const form = ref({
  name: '',
  email: ''
})

const loading = ref(true)
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

async function loadProfile() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/user/profile', {
      credentials: 'same-origin'
    })

    const data = await readResponse(response)

    const user = data.user ?? data.profile ?? data

    if (!user || !user.name || !user.email) {
      throw new Error('Unexpected profile response.')
    }

    profile.value = {
      id: user.id ?? null,
      name: user.name,
      email: user.email,
      role: user.role ?? 'user',
      status: user.status ?? 'approved'
    }

    form.value = {
      name: user.name,
      email: user.email
    }

  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  error.value = ''
  success.value = ''

  const name = form.value.name.trim()
  const email = form.value.email.trim()

  if (!name || !email) {
    error.value = 'Name and email are required.'
    return
  }

  saving.value = true

  try {
    const response = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        name: name,
        email: email
      })
    })

    await readResponse(response)

    // Reload saved values from the database
    await loadProfile()

    if (!error.value) {
      success.value = 'Profile updated successfully.'
    }

  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

function resetForm() {
  form.value = {
    name: profile.value.name,
    email: profile.value.email
  }

  error.value = ''
  success.value = ''
}

onMounted(loadProfile)
</script>

<template>
  <div class="container my-5">

    <!-- Heading -->
    <div class="d-flex flex-wrap justify-content-between
                align-items-center gap-3 mb-4">

      <div>
        <h2 class="text-success fw-bold">
          My Profile
        </h2>

        <p class="text-muted mb-0">
          View and update your account information.
        </p>
      </div>

      <button
        class="btn btn-outline-secondary"
        @click="emit('back')"
      >
        Back to Dashboard
      </button>

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
      <p class="mt-3">Loading profile...</p>
    </div>

    <!-- Profile Form -->
    <div v-else-if="profile.id !== null" class="row justify-content-center">
      <div class="col-md-8 col-lg-7">

        <div class="card shadow-sm border-0">
          <div class="card-body p-4">

            <h4 class="mb-4">Account Information</h4>

            <form @submit.prevent="saveProfile">

              <!-- Name -->
              <div class="mb-3">
                <label for="profileName" class="form-label">
                  Full Name
                </label>

                <input
                  id="profileName"
                  v-model="form.name"
                  type="text"
                  class="form-control"
                  maxlength="100"
                  required
                />
              </div>

              <!-- Email -->
              <div class="mb-3">
                <label for="profileEmail" class="form-label">
                  Email Address
                </label>

                <input
                  id="profileEmail"
                  v-model="form.email"
                  type="email"
                  class="form-control"
                  maxlength="120"
                  required
                />
              </div>

              <!-- Role -->
              <div class="mb-3">
                <label class="form-label">Account Role</label>

                <input
                  :value="profile.role"
                  type="text"
                  class="form-control"
                  disabled
                />
              </div>

              <!-- Status -->
              <div class="mb-4">
                <label class="form-label">Account Status</label>

                <input
                  :value="profile.status"
                  type="text"
                  class="form-control"
                  disabled
                />
              </div>

              <div class="d-flex gap-2">

                <button
                  type="submit"
                  class="btn btn-success"
                  :disabled="saving"
                >
                  {{
                    saving
                      ? 'Saving Changes...'
                      : 'Save Changes'
                  }}
                </button>

                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  :disabled="saving"
                  @click="resetForm"
                >
                  Reset
                </button>

              </div>

            </form>

          </div>
        </div>

      </div>
    </div>

  </div>
</template>
