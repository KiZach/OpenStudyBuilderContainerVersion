<template>
  <v-card elevation="0" class="rounded-0">
    <v-card-text>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.sponsor_compound') }}
        </v-col>
        <v-col cols="2">
          {{ $filters.yesno(compound.is_sponsor_compound) }}
        </v-col>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.is_name_inn') }}
        </v-col>
        <v-col cols="2">
          {{ $filters.yesno(compound.is_name_inn) }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.nnc_number_long') }}
        </v-col>
        <v-col cols="2">
          {{ compound.nnc_long_number }}
        </v-col>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.nnc_number_short') }}
        </v-col>
        <v-col cols="2">
          {{ compound.nnc_short_number }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.analyte_number') }}
        </v-col>
        <v-col cols="2">
          {{ compound.analyte_number }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.compound_aliases') }}
        </v-col>
        <v-col cols="6">
          <v-table>
            <thead>
              <tr class="text-left">
                <th scope="col">
                  {{ $t('CompoundOverview.compound_alias') }}
                </th>
                <th scope="col">
                  {{ $t('_global.definition') }}
                </th>
                <th scope="col">
                  {{ $t('CompoundOverview.preferred_alias') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alias in compoundAliases" :key="alias.uid">
                <td>{{ alias.name }}</td>
                <td>{{ alias.definition }}</td>
                <td>{{ $filters.yesno(alias.is_preferred_synonym) }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('_global.definition') }}
        </v-col>
        <v-col cols="10">
          <div v-html="getHtmlLineBreaks(compound.definition)" />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.brand_name') }}
        </v-col>
        <v-col cols="10">
          <p v-for="brand in compound.brands" :key="brand.uid">
            {{ brand.name }}
          </p>
        </v-col>
      </v-row>
      <div
        v-for="substance in compound.substances"
        :key="substance.substance_term_uid"
        class="my-4 py-4 substance"
      >
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('CompoundOverview.substance_name') }}
          </v-col>
          <v-col cols="2">
            {{ substance.substance_name }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('CompoundOverview.unii') }}
          </v-col>
          <v-col cols="2">
            {{ substance.substance_unii }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('CompoundOverview.pharma_class') }}
          </v-col>
          <v-col cols="2">
            {{ substance.pclass_name }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('CompoundOverview.med_rt') }}
          </v-col>
          <v-col cols="2">
            {{ substance.pclass_id }}
          </v-col>
        </v-row>
      </div>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.dose') }}
        </v-col>
        <v-col cols="6">
          <v-table>
            <thead>
              <tr class="text-left">
                <th scope="col">
                  {{ $t('CompoundOverview.value') }}
                </th>
                <th scope="col">
                  {{ $t('CompoundOverview.unit') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="dose in compound.dose_values" :key="dose.uid">
                <td>{{ dose.value }}</td>
                <td>{{ dose.unit_label }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.strength') }}
        </v-col>
        <v-col cols="6">
          <v-table>
            <thead>
              <tr class="text-left">
                <th scope="col">
                  {{ $t('CompoundOverview.value') }}
                </th>
                <th scope="col">
                  {{ $t('CompoundOverview.unit') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="strength in compound.strength_values"
                :key="strength.uid"
              >
                <td>{{ strength.value }}</td>
                <td>{{ strength.unit_label }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.dosing_freq') }}
        </v-col>
        <v-col cols="10">
          <p
            v-for="doseFreq in compound.dose_frequencies"
            :key="doseFreq.term_uid"
          >
            {{ doseFreq.name }}
          </p>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.route_of_admin') }}
        </v-col>
        <v-col cols="10">
          <p
            v-for="route in compound.routes_of_administration"
            :key="route.term_uid"
          >
            {{ route.name }}
          </p>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.dosage_form') }}
        </v-col>
        <v-col cols="10">
          <p
            v-for="dosageForm in compound.dosage_forms"
            :key="dosageForm.term_uid"
          >
            {{ dosageForm.name }}
          </p>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.dispensed_in') }}
        </v-col>
        <v-col cols="10">
          <p v-for="dispenser in compound.dispensers" :key="dispenser.term_uid">
            {{ dispenser.name }}
          </p>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.device') }}
        </v-col>
        <v-col cols="10">
          <p v-for="device in compound.delivery_devices" :key="device.term_uid">
            {{ device.name }}
          </p>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.half_life') }}
        </v-col>
        <v-col cols="2">
          {{ compound.half_life ? compound.half_life.value : '' }}
        </v-col>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.unit') }}
        </v-col>
        <v-col cols="2">
          {{ compound.half_life ? compound.half_life.unit_label : '' }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.lag_time') }}
        </v-col>
        <v-col cols="6">
          <v-table>
            <thead>
              <tr class="text-left">
                <th scope="col">
                  {{ $t('CompoundOverview.sdtm_domain') }}
                </th>
                <th scope="col">
                  {{ $t('CompoundOverview.value') }}
                </th>
                <th scope="col">
                  {{ $t('CompoundOverview.unit') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lag_time in compound.lag_times" :key="lag_time.uid">
                <td>{{ lag_time.sdtm_domain_label }}</td>
                <td>{{ lag_time.value }}</td>
                <td>{{ lag_time.unit_label }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
import compoundAliases from '@/api/concepts/compoundAliases'

export default {
  props: {
    compound: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      compoundAliases: [],
    }
  },
  watch: {
    compound(value) {
      const params = {
        filters: {
          compound_uid: { v: [value.uid] },
        },
      }
      compoundAliases.getFiltered(params).then((resp) => {
        this.compoundAliases = resp.data.items
      })
    },
  },
  methods: {
    getHtmlLineBreaks(value) {
      return value ? value.replaceAll('\n', '<br />') : ''
    },
  },
}
</script>

<style lang="scss" scoped>
.substance {
  border-bottom: 1px solid var(--v-greyBackground-base);
  border-top: 1px solid var(--v-greyBackground-base);
}
</style>
