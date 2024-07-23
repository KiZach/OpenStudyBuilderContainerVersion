<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyElements.study_element') + ': ' + element.name }}
      <v-chip
        :color="element.element_colour"
        size="small"
        class="mt-2 ml-2"
        variant="flat"
      />
      <v-spacer />
      <v-btn
        size="small"
        :title="$t('_global.close')"
        class="ml-2"
        icon="mdi-close"
        variant="text"
        @click="close"
      />
    </div>
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_short_name') }}
          </v-col>
          <v-col cols="2">
            {{ element.short_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_type') }}
          </v-col>
          <v-col cols="2">
            {{
              element.element_type
                ? element.element_type.sponsor_preferred_name
                : ''
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_sub_type') }}
          </v-col>
          <v-col cols="2">
            {{
              element.element_subtype
                ? element.element_subtype.sponsor_preferred_name
                : ''
            }}
          </v-col>
        </v-row>
        <v-row v-if="element.planned_duration">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.planned_duration') }}
          </v-col>
          <v-col cols="2">
            {{
              element.planned_duration.duration_value +
              ' ' +
              element.planned_duration.duration_unit_code.name
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_start_rule') }}
          </v-col>
          <v-col cols="2">
            {{ element.start_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_end_rule') }}
          </v-col>
          <v-col cols="2">
            {{ element.end_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.description') }}
          </v-col>
          <v-col cols="2">
            {{ element.description }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import arms from '@/api/arms'

export default {
  data() {
    return {
      element: {},
    }
  },
  mounted() {
    arms
      .getStudyElement(this.$route.params.study_id, this.$route.params.id)
      .then((resp) => {
        this.element = resp.data
      })
  },
  methods: {
    close() {
      this.$router.push({ name: 'StudyStructure', params: { tab: 'elements' } })
    },
  },
}
</script>
