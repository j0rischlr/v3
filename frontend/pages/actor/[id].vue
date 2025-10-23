<template>
  <div class="actor-page">
    <div v-if="loading" class="loading-container">
      <div class="loading-bar-container">
        <div class="loading-bar"></div>
      </div>
    </div>

    <div v-else-if="actor" class="actor-container">
      <!-- Header avec photo et infos -->
      <div class="actor-header-new">
        <div class="actor-photo-portrait">
          <img
            v-if="actor.profile_path"
            :src="actor.profile_path"
            :alt="actor.name"
            class="actor-portrait-image"
          />
          <div v-else class="actor-portrait-placeholder">
            {{ actor.name.charAt(0) }}
          </div>
        </div>
        <div class="actor-info-center">
          <h1 class="actor-name-title">{{ actor.name }}</h1>
          <div class="actor-details-info">
            <p v-if="actor.birthday" class="actor-info-item">
              {{ formatBirthday(actor.birthday) }}
            </p>
            <p v-if="actor.place_of_birth" class="actor-info-item">
              {{ actor.place_of_birth }}
            </p>
          </div>
        </div>
      </div>

      <!-- Filmographie -->
      <div class="filmography-section">
        <h2 class="filmography-title">Filmographie</h2>
        <div v-if="actor.filmography && actor.filmography.length > 0" class="movies-grid">
          <NuxtLink
            v-for="movie in actor.filmography"
            :key="movie.id"
            :to="`/movie/${movie.id}`"
            class="movie-card"
          >
            <div class="movie-poster-wrapper">
              <img
                v-if="movie.poster_path"
                :src="movie.poster_path"
                :alt="movie.title"
                class="movie-card-poster"
              />
              <div v-else class="movie-card-placeholder">
                {{ movie.title.charAt(0) }}
              </div>
            </div>
            <div class="movie-card-content">
              <h3 class="movie-card-title">{{ movie.title }}</h3>
              <p v-if="movie.character" class="movie-card-character">
                <em>{{ movie.character }}</em>
              </p>
              <div class="movie-card-meta">
                <span v-if="movie.release_date" class="movie-card-year">
                  {{ formatYear(movie.release_date) }}
                </span>
                <span v-if="movie.vote_average" class="movie-card-rating">
                  ⭐ {{ movie.vote_average.toFixed(1) }}
                </span>
              </div>
            </div>
          </NuxtLink>
        </div>
        <p v-else class="no-movies">Aucun film trouvé pour cet acteur.</p>
      </div>
    </div>

    <div v-else-if="error" class="error-container">
      <h2>Erreur</h2>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const config = useRuntimeConfig()
const actor = ref(null)
const loading = ref(false)
const error = ref(null)

const fetchActorDetails = async () => {
  loading.value = true
  error.value = null

  try {
    const actorId = route.params.id
    const response = await $fetch(`${config.public.apiBaseUrl}/api/actor/${actorId}`)

    // Trier les films par date de sortie (du plus récent au plus ancien)
    if (response.filmography) {
      response.filmography = response.filmography.sort((a, b) => {
        const dateA = a.release_date ? new Date(a.release_date) : new Date(0)
        const dateB = b.release_date ? new Date(b.release_date) : new Date(0)
        return dateB - dateA // Ordre décroissant (plus récent d'abord)
      })
    }

    actor.value = response
  } catch (err) {
    error.value = 'Impossible de charger les informations de l\'acteur.'
    console.error('Erreur:', err)
  } finally {
    loading.value = false
  }
}

const formatYear = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).getFullYear()
}

const formatBirthday = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

onMounted(() => {
  fetchActorDetails()
})
</script>
