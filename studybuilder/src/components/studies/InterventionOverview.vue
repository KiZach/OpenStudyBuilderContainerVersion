<template>
  <div style="overflow-x: auto">
    <v-skeleton-loader
      v-if="studiesCompoundsStore.studyCompounds__Loading"
      class="mx-auto"
      max-width="800px"
      type="table-heading, table-thead, table-tbody"
    />
    <div
      v-if="
        !studiesCompoundsStore.studyCompounds__Loading &&
        !studiesCompoundsStore.studyCompounds.length
      "
      class="mx-4 my-8"
    >
      {{ $t('InterventionOverview.no_intervention_selected') }}
    </div>
    <table
      v-if="
        !studiesCompoundsStore.studyCompounds__Loading &&
        studiesCompoundsStore.studyCompounds.length
      "
      class="mt-4"
      :aria-label="$t('InterventionOverview.table_caption')"
    >
      <thead>
        <tr>
          <th class="no-border" scope="col" />
          <th :colspan="cols" scope="col">
            {{ $t('InterventionOverview.study_compounds') }}
          </th>
        </tr>
        <tr>
          <th scope="col">
            {{ $t('InterventionOverview.first_col_title') }}
          </th>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`header-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.name }}
            </template>
          </td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ $t('InterventionOverview.type_of_treatment') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`tot-${index}`"
          >
            {{
              studyCompound.type_of_treatment
                ? studyCompound.type_of_treatment.name
                : ''
            }}
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.reason_for_missing') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`rfm-${index}`"
          >
            <template v-if="studyCompound.reason_for_missing_null_value">
              {{ studyCompound.reason_for_missing_null_value.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.sponsor_compound') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`sc-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ $filters.yesno(studyCompound.compound.is_sponsor_compound) }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_number_long') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`cnl-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.nnc_long_number }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_number_short') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`cns-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.nnc_short_number }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.analyte_number') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`aln-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.analyte_number }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.is_inn') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`inn-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ $filters.yesno(studyCompound.compound.is_name_inn) }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.substances') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`sub-${index}`"
            class="no-padding"
          >
            <table v-if="studyCompound.compound" class="no-border">
              <tbody>
                <tr
                  v-for="(substance, subIndex) in studyCompound.compound
                    .substances"
                  :key="`sub-${index}-${subIndex}`"
                  :class="{ 'border-top': subIndex > 0 }"
                >
                  <td class="no-border half-size">
                    {{ substance.substance_name }} ({{
                      substance.substance_unii
                    }})
                  </td>
                  <td class="border-left half-size">
                    {{ substance.pclass_name }} ({{ substance.pclass_id }})
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_aliases') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`alias-${index}`"
            class="no-padding"
          >
            <table v-if="studyCompound.compound" class="no-border">
              <tbody>
                <tr
                  v-for="(alias, aliasIndex) in compoundAliases[
                    studyCompound.compound.uid
                  ]"
                  :key="`alias-${index}-${aliasIndex}`"
                  class="no-padding"
                  :class="{ 'border-top': aliasIndex > 0 }"
                >
                  <td class="no-border">
                    {{ alias.name }} ({{
                      $filters.yesno(alias.is_preferred_synonym)
                    }})
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.strength') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`strength-${index}`"
          >
            <template v-if="studyCompound.strength_value">
              {{ studyCompound.strength_value.value }} ({{
                studyCompound.strength_value.unit_label
              }})
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.pharmaceutical_dosage_form') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`dosage-${index}`"
          >
            <template v-if="studyCompound.dosage_form">
              {{ studyCompound.dosage_form.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.route_of_admin') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`roa-${index}`"
          >
            <template v-if="studyCompound.route_of_administration">
              {{ studyCompound.route_of_administration.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.dispensed_in') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`dispensed-${index}`"
          >
            <template v-if="studyCompound.dispensed_in">
              {{ studyCompound.dispensed_in.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.delivery_device') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`device-${index}`"
          >
            <template v-if="studyCompound.device">
              {{ studyCompound.device.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_dosing') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`dosing-${index}`"
            class="no-padding"
          >
            <table
              v-if="
                studiesCompoundsStore.studyCompoundDosings[
                  studyCompound.study_compound_uid
                ]
              "
              class="no-border"
            >
              <tr
                v-for="(compoundDosing, dosingIndex) in studiesCompoundsStore
                  .studyCompoundDosings[studyCompound.study_compound_uid]"
                :key="`lg-${index}-${dosingIndex}`"
                :class="{ 'border-top': dosingIndex > 0 }"
              >
                <td class="no-border half-size">
                  {{ compoundDosing.study_element.name }}
                </td>
                <td class="border-left half-size">
                  <template v-if="compoundDosing.dose_value">
                    {{ compoundDosing.dose_value.value }}
                    {{ compoundDosing.dose_value.unit_label
                    }}{{ compoundDosing.dose_frequency ? ',' : '' }}
                  </template>
                  <template v-if="compoundDosing.dose_frequency">
                    <template v-if="compoundDosing.dose_value">
                      {{ compoundDosing.dose_frequency.name }}
                    </template>
                    <template v-else>
                      {{ compoundDosing.dose_frequency.name }}
                    </template>
                  </template>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.half_life') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`hl-${index}`"
          >
            <template
              v-if="studyCompound.compound && studyCompound.compound.half_life"
            >
              <div v-if="studyCompound.compound.half_life.value">
                {{ studyCompound.compound.half_life.value }} ({{
                  studyCompound.compound.half_life.unit_label
                }})
              </div>
              <div v-else>
                {{ studyCompound.compound.half_life }}
              </div>
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.lag_time') }}</td>
          <td
            v-for="(
              studyCompound, lgIndex
            ) in studiesCompoundsStore.studyCompounds"
            :key="`lg-${lgIndex}`"
            class="no-padding"
          >
            <table
              v-if="studyCompound.compound && studyCompound.compound.lag_times"
              class="no-border"
            >
              <tr
                v-for="(lagTime, index) in studyCompound.compound.lag_times"
                :key="`lg-${lgIndex}-${index}`"
                :class="{ 'border-top': index > 0 }"
              >
                <td class="no-border half-size">
                  {{ lagTime.value }} ({{ lagTime.unit_label }})
                </td>
                <td class="border-left half-size">
                  {{ lagTime.sdtm_domain_label }}
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_def') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`def-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.definition }}
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { computed } from 'vue'
import compoundAliases from '@/api/concepts/compoundAliases'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  setup() {
    const studiesCompoundsStore = useStudiesCompoundsStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studiesCompoundsStore,
    }
  },
  data() {
    return {
      compoundAliases: {},
    }
  },
  computed: {
    cols() {
      return this.studiesCompoundsStore.studyCompounds.length
        ? this.studiesCompoundsStore.studyCompounds.length
        : 1
    },
  },
  watch: {
    studyCompounds() {
      this.getAllCompoundAliases()
    },
  },
  mounted() {
    this.studiesCompoundsStore
      .fetchStudyCompounds({
        studyUid: this.selectedStudy.uid,
        page_size: 0,
      })
      .then(() => {
        this.getAllCompoundAliases()
      })
    this.studiesCompoundsStore.fetchStudyCompoundDosings(
      this.selectedStudy.uid,
      0
    )
  },
  methods: {
    getCompoundAliases(compoundUid) {
      const params = {
        filters: {
          compound_uid: { v: [compoundUid], op: 'eq' },
        },
      }
      compoundAliases.getFiltered(params).then((resp) => {
        this.compoundAliases[compoundUid] = resp.data.items
      })
    },
    getAllCompoundAliases() {
      for (const studyCompound of this.studiesCompoundsStore.studyCompounds) {
        if (
          !studyCompound.compound ||
          this.compoundAliases[studyCompound.compound.uid] !== undefined
        ) {
          continue
        }
        this.compoundAliases[studyCompound.compound.uid] = []
        this.getCompoundAliases(studyCompound.compound.uid)
      }
    },
  },
}
</script>

<style scoped lang="scss">
table {
  width: 100%;
  text-align: left;

  border-spacing: 0px;
  border-collapse: collapse;
}
.no-border {
  border: 0 !important;
}
.border-left {
  border: 0;
  border-left: 1px solid black;
}
.border-top {
  border: 0;
  border-top: 1px solid black;
}
.no-padding {
  padding: 0;
}
.half-size {
  width: 50%;
}
tr {
  padding: 4px;
}
td,
th {
  border: 1px solid black;
  padding: 4px;
}
</style>
