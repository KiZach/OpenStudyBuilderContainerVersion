<template>
  <div>
    <div class="mt-4 mb-6 d-flex align-center">
      <v-spacer />
      <v-menu location="start">
        <template #activator="{ props }">
          <div>
            <v-btn
              data-cy="table-item-action-button"
              icon="mdi-menu"
              color="primary"
              v-bind="props"
              class="pb-3"
            />
          </div>
        </template>
        <v-card elevation="0" color="transparent" class="mt-n1">
          <v-card-item>
            <div class="mb-1">
              <DataTableExportButton type="endpoint" data-url="" />
              <v-btn
                v-if="codelistAttributes.extensible"
                class="mx-2"
                size="small"
                color="primary"
                :title="$t('CodelistTermDetail.add_term')"
                icon="mdi-plus"
                @click.stop="showCreationForm = true"
              />
            </div>
          </v-card-item>
        </v-card>
      </v-menu>
    </div>
    <CodelistSummary
      :codelist-names="codelistNames"
      :codelist-attributes="codelistAttributes"
    />
    <div class="pa-4 v-label">
      {{ $t('CodelistTermDetail.sponsor_title') }}
    </div>
    <v-table :aria-label="$t('CodelistTermDetail.sponsor_title')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="25%">
            {{ $t('CodeListDetail.ct_identifiers') }}
          </th>
          <th width="50%">
            {{ $t('CodeListDetail.selected_values') }}
          </th>
          <th width="5%">
            {{ $t('_global.status') }}
          </th>
          <th width="10%">
            {{ $t('_global.modified') }}
          </th>
          <th width="5%">
            {{ $t('_global.version') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ $t('CodeListDetail.sponsor_pref_name') }}</td>
          <td>{{ termNames.sponsor_preferred_name }}</td>
          <td data-cy="names-status" rowspan="2">
            <StatusChip :status="termNames.status" />
          </td>
          <td rowspan="2">
            {{ $filters.date(termNames.start_date) }}
          </td>
          <td data-cy="names-version" rowspan="2">
            {{ termNames.version }}
          </td>
          <td rowspan="2">
            <v-btn
              v-if="
                termNames.possible_actions.find((action) => action === 'edit')
              "
              data-cy="edit-sponsor-values"
              icon="mdi-pencil-outline"
              color="primary"
              :title="$t('CodelistTermDetail.edit_names')"
              variant="text"
              @click="showNamesForm = true"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'approve'
                )
              "
              data-cy="approve-term-sponsor-values"
              color="success"
              icon="mdi-check-decagram"
              :title="$t('CodelistTermDetail.approve_names')"
              variant="text"
              @click="approveTermNames"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'new_version'
                )
              "
              data-cy="create-new-sponsor-values"
              color="primary"
              icon="mdi-plus-circle-outline"
              :title="$t('CodelistTermDetail.new_names_version')"
              variant="text"
              @click="newTermNamesVersion"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'inactivate'
                )
              "
              color="warning"
              icon="mdi-close-octagon-outline"
              :title="$t('CodelistTermDetail.inactivate_names')"
              variant="text"
              @click="inactivateTermNames"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'reactivate'
                )
              "
              color="primary"
              icon="mdi-undo-variant"
              :title="$t('CodelistTermDetail.reactivate_names')"
              variant="text"
              @click="reactivateTermNames"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find((action) => action === 'delete')
              "
              icon="mdi-delete-outline"
              color="error"
              :title="$t('CodelistTermDetail.delete_names')"
              variant="text"
              @click="deleteTermNames()"
            />
            <v-btn
              data-cy="term-sponsor-version-history"
              icon="mdi-history"
              :title="$t('CodeListDetail.history')"
              variant="text"
              @click="openSponsorValuesHistory"
            />
          </td>
        </tr>
        <tr>
          <td>{{ $t('CodelistTermDetail.sentence_case_name') }}</td>
          <td>{{ termNames.sponsor_preferred_name_sentence_case }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodelistTermDetail.order') }}</td>
          <td>{{ getTermOrderInCodelist(termNames, codelistUid) }}</td>
        </tr>
      </tbody>
    </v-table>

    <div class="v-label pa-4 mt-6">
      {{ $t('CodelistTermDetail.attributes_title') }}
    </div>
    <v-table :aria-label="$t('CodelistTermDetail.attributes_title')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="25%">
            {{ $t('CodeListDetail.ct_identifiers') }}
          </th>
          <th width="50%">
            {{ $t('CodeListDetail.selected_values') }}
          </th>
          <th width="5%">
            {{ $t('_global.status') }}
          </th>
          <th width="10%">
            {{ $t('_global.modified') }}
          </th>
          <th width="5%">
            {{ $t('_global.version') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ $t('CodelistTermDetail.concept_id') }}</td>
          <td>{{ termAttributes.term_uid }}</td>
          <td data-cy="attributes-status" rowspan="5">
            <StatusChip :status="termAttributes.status" />
          </td>
          <td rowspan="5">
            {{ $filters.date(termAttributes.start_date) }}
          </td>
          <td data-cy="attributes-version" rowspan="5">
            {{ termAttributes.version }}
          </td>
          <td rowspan="5">
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'edit'
                )
              "
              icon="mdi-pencil-outline"
              color="primary"
              variant="text"
              :title="$t('CodelistTermDetail.edit_attributes')"
              @click="showAttributesForm = true"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'approve'
                )
              "
              data-cy="approve-term-attributes-values"
              color="success"
              icon="mdi-check-decagram"
              :title="$t('CodelistTermDetail.approve_attributes')"
              variant="text"
              @click="approveTermAttributes"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'new_version'
                )
              "
              color="primary"
              icon="mdi-plus-circle-outline"
              :title="$t('CodelistTermDetail.new_attributes_version')"
              variant="text"
              @click="newTermAttributesVersion"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'inactivate'
                )
              "
              color="warning"
              icon="mdi-close-octagon-outline"
              :title="$t('CodelistTermDetail.inactivate_attributes')"
              variant="text"
              @click="inactivateTermAttributes"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'reactivate'
                )
              "
              color="primary"
              icon="mdi-undo-variant"
              :title="$t('CodelistTermDetail.reactivate_attributes')"
              variant="text"
              @click="reactivateTermAttributes"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'delete'
                )
              "
              icon="mdi-delete-outline"
              color="error"
              :title="$t('CodelistTermDetail.delete_attributes')"
              variant="text"
              @click="deleteTermAttributes()"
            />
            <v-btn
              icon="mdi-history"
              :title="$t('CodeListDetail.history')"
              variant="text"
              @click="openCTValuesHistory"
            />
          </td>
        </tr>
        <tr>
          <td>{{ $t('CodelistTermDetail.name_submission_value') }}</td>
          <td>{{ termAttributes.name_submission_value }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodelistTermDetail.code_submission_value') }}</td>
          <td>{{ termAttributes.code_submission_value }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodelistTermDetail.nci_pref_name') }}</td>
          <td>{{ termAttributes.nci_preferred_name }}</td>
        </tr>
        <tr>
          <td>{{ $t('_global.definition') }}</td>
          <td>{{ termAttributes.definition }}</td>
        </tr>
      </tbody>
    </v-table>
    <v-dialog
      v-model="showNamesForm"
      persistent
      max-width="1024px"
      @keydown.esc="showNamesForm = false"
    >
      <CodelistTermNamesForm
        v-model="termNames"
        :codelist-uid="codelistUid"
        @close="showNamesForm = false"
      />
    </v-dialog>
    <v-dialog
      v-model="showAttributesForm"
      persistent
      max-width="1024px"
      @keydown.esc="showAttributesForm = false"
    >
      <CodelistTermAttributesForm
        v-model="termAttributes"
        @close="showAttributesForm = false"
      />
    </v-dialog>
    <v-dialog
      v-if="codelistAttributes.extensible"
      v-model="showCreationForm"
      persistent
      max-width="1024px"
      content-class="top-dialog"
    >
      <CodelistTermCreationForm
        :catalogue-name="codelistNames.catalogue_name"
        :codelist-uid="codelistNames.codelist_uid"
        @close="showCreationForm = false"
        @created="goToTerm"
      />
    </v-dialog>
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="historyTitleLabel"
        :headers="historyHeaders"
        :items="historyItems"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import CodelistSummary from '@/components/library/CodelistSummary.vue'
import CodelistTermAttributesForm from '@/components/library/CodelistTermAttributesForm.vue'
import CodelistTermCreationForm from '@/components/library/CodelistTermCreationForm.vue'
import CodelistTermNamesForm from '@/components/library/CodelistTermNamesForm.vue'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import codelists from '@/utils/codelists'

export default {
  components: {
    CodelistSummary,
    CodelistTermAttributesForm,
    CodelistTermCreationForm,
    CodelistTermNamesForm,
    DataTableExportButton,
    HistoryTable,
    StatusChip,
  },
  inject: ['eventBusEmit'],
  props: {
    codelistUid: {
      type: String,
      default: null,
    },
    termUid: {
      type: String,
      default: null,
    },
  },
  setup() {
    return {
      getTermOrderInCodelist: codelists.getTermOrderInCodelist,
    }
  },
  data() {
    return {
      actionsMenu: false,
      codelistAttributes: {},
      codelistNames: {},
      historyType: '',
      historyItems: [],
      historyHeaders: [],
      showAttributesForm: false,
      showCreationForm: false,
      showHistory: false,
      showNamesForm: false,
      term: { term_uid: this.termUid },
      termNames: { possible_actions: [] },
      termAttributes: { possible_actions: [] },
    }
  },
  computed: {
    historyTitleLabel() {
      return this.historyType === 'termName'
        ? this.$t('CodelistTermTable.history_label_name', {
            term: this.termUid,
          })
        : this.$t('CodelistTermTable.history_label_attributes', {
            term: this.termUid,
          })
    },
  },
  mounted() {
    controlledTerminology.getCodelistNames(this.codelistUid).then((resp) => {
      this.codelistNames = resp.data
    })
    controlledTerminology
      .getCodelistAttributes(this.codelistUid)
      .then((resp) => {
        this.codelistAttributes = resp.data
      })
    this.fetchTermNames()
    this.fetchTermAttributes()
  },
  methods: {
    fetchTermNames() {
      controlledTerminology.getCodelistTermNames(this.termUid).then((resp) => {
        this.termNames = resp.data
      })
    },
    newTermNamesVersion() {
      controlledTerminology
        .newCodelistTermNamesVersion(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.new_names_version_success'),
          })
        })
    },
    approveTermNames() {
      controlledTerminology
        .approveCodelistTermNames(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.approve_names_success'),
          })
        })
    },
    inactivateTermNames() {
      controlledTerminology
        .inactivateCodelistTermNames(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.inactivate_names_success'),
          })
        })
    },
    reactivateTermNames() {
      controlledTerminology
        .reactivateCodelistTermNames(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.reactivate_names_success'),
          })
        })
    },
    deleteTermNames() {
      controlledTerminology
        .deleteCodelistTermNames(this.termNames.term_uid)
        .then(() => {
          this.fetchTermNames()
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.delete_names_success'),
          })
        })
    },
    fetchTermAttributes() {
      controlledTerminology
        .getCodelistTermAttributes(this.termUid)
        .then((resp) => {
          this.termAttributes = resp.data
        })
    },
    newTermAttributesVersion() {
      controlledTerminology
        .newCodelistTermAttributesVersion(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.new_attributes_version_success'),
          })
        })
    },
    approveTermAttributes() {
      controlledTerminology
        .approveCodelistTermAttributes(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.approve_attributes_success'),
          })
        })
    },
    inactivateTermAttributes() {
      controlledTerminology
        .inactivateCodelistTermAttributes(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.inactivate_attributes_success'),
          })
        })
    },
    reactivateTermAttributes() {
      controlledTerminology
        .reactivateCodelistTermAttributes(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.reactivate_attributes_success'),
          })
        })
    },
    deleteTermAttributes() {
      controlledTerminology
        .deleteCodelistTermAttributes(this.termNames.term_uid)
        .then(() => {
          this.fetchTermAttributes()
          this.eventBusEmit('notification', {
            msg: this.$t('CodelistTermDetail.delete_attributes_success'),
          })
        })
    },
    goToTerm(term) {
      this.$router.push({
        name: 'CodelistTermDetail',
        params: { codelist_id: term.codelist_uid, term_id: term.term_uid },
      })
      this.eventBusEmit('notification', {
        msg: this.$t('CodelistTermCreationForm.add_success'),
      })
    },
    async openSponsorValuesHistory() {
      this.historyType = 'termName'
      this.historyHeaders = [
        {
          title: this.$t('CodeListDetail.sponsor_pref_name'),
          key: 'sponsor_preferred_name',
        },
        {
          title: this.$t('CodelistTermDetail.sentence_case_name'),
          key: 'sponsor_preferred_name_sentence_case',
        },
        { title: this.$t('CodelistTermDetail.order'), key: 'order' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
      ]
      const resp = await controlledTerminology.getCodelistTermNamesVersions(
        this.termUid
      )

      this.historyItems = resp.data.map((item) => {
        item.order = this.getTermOrderInCodelist(item, this.codelistUid)
        return item
      })
      this.showHistory = true
    },
    async openCTValuesHistory() {
      this.historyType = 'termAttributes'
      this.historyHeaders = [
        { title: this.$t('CodelistTermDetail.concept_id'), key: 'term_uid' },
        {
          title: this.$t('CodelistTermDetail.name_submission_value'),
          key: 'name_submission_value',
        },
        {
          title: this.$t('CodelistTermDetail.code_submission_value'),
          key: 'code_submission_value',
        },
        {
          title: this.$t('CodeListDetail.nci_pref_name'),
          key: 'nci_preferred_name',
        },
        { title: this.$t('_global.definition'), key: 'definition' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
      ]
      const resp =
        await controlledTerminology.getCodelistTermAttributesVersions(
          this.termUid
        )
      this.historyItems = resp.data
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
      this.historyType = ''
    },
  },
}
</script>
