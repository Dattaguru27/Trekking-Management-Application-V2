
<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login-success'])

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function login() {
  error.value = ''
  loading.value = true

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        email: email.value,
        password: password.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      error.value = data.message || 'Login failed.'
      return
    }

    // Verify the logged-in account using Flask session
    const meResponse = await fetch('/api/auth/me', {
      credentials: 'same-origin'
    })

    const meData = await meResponse.json()

    if (!meResponse.ok) {
      error.value = meData.message || 'Could not verify session.'
      return
    }

    // Extract role from the session response
    const role = meData.user?.role ?? meData.role

    if (!['admin', 'staff', 'user'].includes(role)) {
      error.value = 'Could not determine account role.'
      return
    }

    emit('login-success', role)

  } catch (err) {
    error.value = 'Cannot connect to the server.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container my-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow border-0">
          <div class="card-body p-4">
            <h2 class="text-center text-success mb-4">
              Login
            </h2>

            <div
              v-if="error"
              class="alert alert-danger"
              role="alert"
            >
              {{ error }}
            </div>

            <form @submit.prevent="login">
              <div class="mb-3">
                <label for="loginEmail" class="form-label">
                  Email Address
                </label>

                <input
                  id="loginEmail"
                  v-model="email"
                  type="email"
                  class="form-control"
                  placeholder="Enter your email"
                  autocomplete="username"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="loginPassword" class="form-label">
                  Password
                </label>

                <input
                  id="loginPassword"
                  v-model="password"
                  type="password"
                  class="form-control"
                  placeholder="Enter your password"
                  autocomplete="current-password"
                  required
                />
              </div>

              <button
                type="submit"
                class="btn btn-success w-100"
                :disabled="loading"
              >
                {{ loading ? 'Logging in...' : 'Login' }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
