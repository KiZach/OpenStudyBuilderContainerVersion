<template>
  <v-card data-cy="form-body" color="white">
    <v-card-title>
      <span class="dialog-title">{{ $t('StudyQuickSelectForm.title') }}</span>
    </v-card-title>
    <v-card-text>
      <v-form ref="observer">
        <v-row class="mt-4">
          <v-col cols="6">
            <v-autocomplete
              v-model="studyById"
              :label="$t('StudyQuickSelectForm.study_id')"
              :items="studiesWithId"
              item-title="current_metadata.identification_metadata.study_id"
              return-object
              :rules="[(value) => formRules.atleastone(value, studyByAcronym)]"
              clearable
              @update:model-value="autoPopulateAcronym"
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-model="studyByAcronym"
              :label="$t('StudyQuickSelectForm.study_acronym')"
              :items="studiesWithAcronym"
              item-title="current_metadata.identification_metadata.study_acronym"
              return-object
              :rules="[(value) => formRules.atleastone(value, studyById)]"
              clearable
              @update:model-value="autoPopulateId"
            />
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
    <v-spacer v-if="expand || expand2" class="distance" />
    <v-card-actions class="pb-4">
      <v-spacer />
      <v-btn class="secondary-btn" color="white" elevation="3" @click="close">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn color="secondary" variant="flat" elevation="3" @click="select">
        {{ $t('_global.ok') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  inject: ['formRules'],
  emits: ['close', 'selected'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      studiesGeneralStore,
    }
  },
  data() {
    return {
      studyById: null,
      studyByAcronym: null,
      studies: [],
      expand: false,
      expand2: false,
    }
  },
  computed: {
    studiesWithId() {
      return this.studies.filter(
        (study) =>
          study.current_metadata.identification_metadata.study_id !== null
      )
    },
    studiesWithAcronym() {
      return this.studies.filter(
        (study) =>
          study.current_metadata.identification_metadata.study_acronym !== null
      )
    },
  },
  mounted() {
    const params = {
      sort_by: { 'current_metadata.identification_metadata.study_id': true },
      page_size: 0,
    }
    study.get(params).then((resp) => {
      this.studies = resp.data.items
    })
  },
  methods: {
    close() {
      this.$emit('close')
    },
    async select() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      if (this.studyById) {
        this.studiesGeneralStore.selectStudy(this.studyById)
      } else {
        this.studiesGeneralStore.selectStudy(this.studyByAcronym)
      }
      this.$emit('selected')
      this.close()
    },
    autoPopulateAcronym(study) {
      if (
        study &&
        study.current_metadata.identification_metadata.study_acronym
      ) {
        this.studyByAcronym = study
      }
    },
    autoPopulateId(study) {
      if (study && study.current_metadata.identification_metadata.study_id) {
        this.studyById = study
      }
    },
  },
}
</script>

<style scoped>
.distance {
  margin-bottom: 260px;
}
</style>
