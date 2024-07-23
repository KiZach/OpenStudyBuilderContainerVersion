<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyCompoundTable.study_compound') }}
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
    <v-card v-if="loaded" elevation="0" class="rounded-0">
      <v-card-text>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.type_of_treatment') }}
          </v-col>
          <v-col cols="2">
            {{
              compound.type_of_treatment ? compound.type_of_treatment.name : ''
            }}
          </v-col>
        </v-row>
        <v-row v-if="compound.reason_for_missing_null_value">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.reason_for_missing') }}
          </v-col>
          <v-col cols="2">
            {{ compound.reason_for_missing_null_value.name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.compound') }}
          </v-col>
          <v-col cols="2">
            {{ compound.compound.name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.sponsor_compound') }}
          </v-col>
          <v-col cols="2">
            {{ $filters.yesno(compound.compound.is_sponsor_compound) }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.is_name_inn') }}
          </v-col>
          <v-col cols="2">
            {{ $filters.yesno(compound.compound.is_name_inn) }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.substance') }}
          </v-col>
          <v-col cols="">
            {{
              compound.compound.substances
                .map((el) => el.substance_name + ` (${el.substance_unii})`)
                .join(', ')
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.compound_alias') }}
          </v-col>
          <v-col cols="2">
            {{ compound.compound_alias ? compound.compound_alias.name : '' }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.preferred_alias') }}
          </v-col>
          <v-col v-if="compound.compound_alias" cols="2">
            {{ $filters.yesno(compound.compound_alias.is_preferred_synonym) }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.strength') }}
          </v-col>
          <v-col v-if="compound.strength_value" cols="2">
            {{
              `${compound.strength_value.value} ${compound.strength_value.unit_label}`
            }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.dosage_form') }}
          </v-col>
          <v-col cols="2">
            {{ compound.dosage_form ? compound.dosage_form.name : '' }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.route_of_admin') }}
          </v-col>
          <v-col cols="2">
            {{
              compound.route_of_administration
                ? compound.route_of_administration.name
                : ''
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.dispensed_in') }}
          </v-col>
          <v-col cols="2">
            {{ compound.dispensed_in ? compound.dispensed_in.name : '' }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.device') }}
          </v-col>
          <v-col cols="2">
            {{
              compound.compound.delivery_devices
                ? compound.compound.delivery_devices
                    .map((el) => el.name)
                    .join(', ')
                : ''
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.half_life') }}
          </v-col>
          <v-col cols="2">
            {{
              `${compound.compound.half_life.value} ${compound.compound.half_life.unit_label}`
            }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.lag_time') }}
          </v-col>
          <v-col cols="2">
            {{
              compound.compound.lag_times
                .map((el) => el.value + el.unit_label)
                .join(', ')
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.nnc_number_long') }}
          </v-col>
          <v-col cols="2">
            {{ compound.compound.nnc_long_number }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.nnc_number_short') }}
          </v-col>
          <v-col cols="2">
            {{ compound.compound.nnc_short_number }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.analyte_number') }}
          </v-col>
          <v-col cols="2">
            {{ compound.compound.analyte_number }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.compound_definition') }}
          </v-col>
          <v-col cols="4">
            {{ compound.compound.definition }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCompoundTable.alias_definition') }}
          </v-col>
          <v-col cols="4">
            {{
              compound.compound_alias ? compound.compound_alias.definition : ''
            }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import study from '@/api/study'
import { computed } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      compound: {},
      loaded: false,
    }
  },
  mounted() {
    study
      .getStudyCompound(this.$route.params.study_id, this.$route.params.id)
      .then((resp) => {
        this.compound = resp.data
        this.loaded = true
      })
  },
  methods: {
    close() {
      this.$router.go(-1)
    },
  },
}
</script>
