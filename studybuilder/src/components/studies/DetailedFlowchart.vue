<template>
  <div
    v-if="!loadingSoaContent"
    v-resize="onResize"
    class="pa-4 bg-white"
    style="overflow-x: auto"
  >
    <v-menu
      v-if="footnoteMode"
      v-model="footnoteMode"
      persistent
      no-click-animation
      :close-on-content-click="false"
      max-height="800px"
      offset-y
      content-class="footnote-center"
    >
      <v-card width="1000px" min-height="150px">
        <v-card-title class="dialog-title d-flex align-center">
          {{ $t('StudyFootnoteEditForm.select_footnote_items') }}
          <v-spacer />
          <v-btn
            color="success"
            icon="mdi-content-save-outline"
            :loading="footnoteUpdateLoading"
            variant="text"
            @click="saveElementsForFootnote"
          />
          <v-btn
            color="primary"
            icon="mdi-close"
            variant="text"
            @click="disableFootnoteMode"
          />
        </v-card-title>
        <v-divider />
        <v-card flat class="bg-parameterBackground mx-3 mt-3">
          <v-card-text class="pa-2">
            <NNParameterHighlighter
              :name="
                activeFootnote.footnote
                  ? activeFootnote.footnote.name
                  : activeFootnote.footnote_template.name
              "
            />
          </v-card-text>
        </v-card>
      </v-card>
    </v-menu>
    <div class="d-flex align-center mb-4">
      <v-switch
        v-model="expandAllRows"
        :label="$t('DetailedFlowchart.expand_all')"
        hide-details
        class="ml-2 flex-grow-0"
        color="primary"
        @update:model-value="toggleAllRowState"
      />
      <v-spacer />
      <template v-if="!readOnly">
        <v-btn
          v-show="multipleConsecutiveVisitsSelected()"
          size="small"
          class="mr-2"
          :title="$t('GroupStudyVisits.title')"
          :disabled="
            footnoteMode ||
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          :loading="soaContentLoadingStore.loading"
          icon="mdi-arrow-expand-horizontal"
          @click="groupSelectedVisits()"
        />
        <v-menu
          v-model="showEditForm"
          :close-on-content-click="false"
          max-height="800px"
          max-width="500px"
          offset-y
          content-class="mt-4"
        >
          <template #activator="{ props }">
            <div>
              <v-btn
                color="primary"
                size="small"
                class="mr-2"
                v-bind="props"
                :disabled="
                  footnoteMode ||
                  !checkPermission($roles.STUDY_WRITE) ||
                  selectedStudyVersion !== null
                "
                icon="mdi-pencil-outline"
              />
            </div>
          </template>
          <v-card color="dfltBackground">
            <v-card-text>
              <v-btn block class="mb-2" @click="redirectTo('epochs')">
                <v-icon left> mdi-arrow-top-right-bold-box-outline </v-icon>
                {{ $t('DetailedFlowchart.study_epochs') }}
              </v-btn>
              <v-btn block class="mb-2" @click="redirectTo('visits')">
                <v-icon left> mdi-arrow-top-right-bold-box-outline </v-icon>
                {{ $t('DetailedFlowchart.study_visits') }}
              </v-btn>
              <v-btn block class="mb-2" @click="redirectTo('activities')">
                <v-icon left> mdi-arrow-top-right-bold-box-outline </v-icon>
                {{ $t('DetailedFlowchart.study_activities') }}
              </v-btn>
              <v-btn block class="mb-2" @click="redirectTo('footnotes')">
                <v-icon left> mdi-arrow-top-right-bold-box-outline </v-icon>
                {{ $t('DetailedFlowchart.soa_footnotes') }}
              </v-btn>
              <v-btn block class="mb-2" @click="redirectTo('instructions')">
                <v-icon left> mdi-arrow-top-right-bold-box-outline </v-icon>
                {{ $t('DetailedFlowchart.activity_instructions') }}
              </v-btn>
            </v-card-text>
          </v-card>
        </v-menu>
        <v-btn
          size="small"
          :title="$t('DetailedFlowchart.hide_activity_selection')"
          :disabled="
            footnoteMode ||
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-eye-off-outline"
          :loading="soaContentLoadingStore.loading"
          @click="toggleActivitySelectionDisplay(false)"
        />
        <v-btn
          size="small"
          color="success"
          :title="$t('DetailedFlowchart.show_activity_selection')"
          class="ml-2"
          :disabled="
            footnoteMode ||
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-eye-outline"
          :loading="soaContentLoadingStore.loading"
          @click="toggleActivitySelectionDisplay(true)"
        />
        <v-btn
          size="small"
          color="primary"
          :title="$t('DetailedFlowchart.edit_activity_selection')"
          class="ml-2"
          :disabled="
            footnoteMode ||
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-pencil-box-multiple-outline"
          :loading="soaContentLoadingStore.loading"
          @click="openBatchEditForm"
        />
        <v-menu rounded location="bottom">
          <template #activator="{ props }">
            <v-btn
              size="small"
              color="nnGreen1"
              class="ml-2 text-white"
              v-bind="props"
              :title="$t('DataTableExportButton.export')"
              icon="mdi-download-outline"
              :loading="soaContentLoadingStore.loading"
            />
          </template>
          <v-list>
            <v-list-item link @click="downloadCSV">
              <v-list-item-title>CSV</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadEXCEL">
              <v-list-item-title>EXCEL</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadDOCX">
              <v-list-item-title>DOCX</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
        <v-btn
          class="ml-2"
          color="secondary"
          size="small"
          :title="$t('NNTableTooltips.history')"
          icon="mdi-history"
          @click="openHistory"
        />
      </template>
    </div>
    <div
      ref="tableContainer"
      class="sticky-header"
      :style="`height: ${tableHeight}px`"
    >
      <table :aria-label="$t('DetailedFlowchart.table_caption')">
        <thead>
          <tr ref="firstHeader">
            <th width="2%" rowspan="4" scope="col" />
            <th width="25%" rowspan="4" scope="col">
              {{ $t('DetailedFlowchart.activities') }}
            </th>
            <th width="10%" scope="col">
              {{ $t('DetailedFlowchart.study_epoch') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaEpochRow"
                :key="`epoch-${index}`"
                class="text-vertical"
                scope="col"
              >
                <v-badge
                  color="transparent"
                  text-color="secondary"
                  floating
                  :content="
                    cell.refs ? getElementFootnotes(cell.refs[0].uid) : ''
                  "
                  class="mt-3 mr-1"
                >
                  {{ cell.text }}
                </v-badge>
                <v-btn
                  v-if="
                    footnoteMode &&
                    cell.text !== '' &&
                    !checkIfElementHasFootnote(cell.refs[0].uid)
                  "
                  size="x-small"
                  icon="mdi-plus"
                  class="mx-0 px-0"
                  color="primary"
                  variant="text"
                  @click="addElementForFootnote(cell.refs[0].uid, 'StudyEpoch')"
                />
                <v-btn
                  v-else-if="
                    footnoteMode &&
                    cell.text !== '' &&
                    checkIfElementHasFootnote(cell.refs[0].uid)
                  "
                  size="x-small"
                  icon="mdi-close"
                  class="mx-0 px-0"
                  color="red"
                  variant="text"
                  @click="removeElementForFootnote(cell.refs[0].uid)"
                />
              </th>
            </template>
            <template v-else>
              <th colspan="2" scope="col" />
            </template>
          </tr>
          <tr ref="secondHeader">
            <th :style="`top: ${firstHeaderHeight}px`" scope="col">
              {{ $t('DetailedFlowchart.visit_short_name') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaVisitRow"
                :key="`shortName-${index}`"
                :style="`top: ${firstHeaderHeight}px`"
                scope="col"
              >
                <div class="d-flex align-center">
                  <v-badge
                    color="transparent"
                    text-color="secondary"
                    floating
                    :content="
                      cell.refs.length
                        ? getElementFootnotes(cell.refs[0].uid)
                        : ''
                    "
                    class="visitFootnote"
                  >
                    {{ cell.text }}
                  </v-badge>
                  <v-btn
                    v-if="
                      footnoteMode &&
                      !checkIfElementHasFootnote(cell.refs[0].uid)
                    "
                    size="x-small"
                    icon="mdi-plus"
                    class="mx-0 px-0"
                    variant="text"
                    @click="
                      addElementForFootnote(cell.refs[0].uid, 'StudyVisit')
                    "
                  />
                  <v-btn
                    v-else-if="
                      footnoteMode &&
                      checkIfElementHasFootnote(cell.refs[0].uid)
                    "
                    size="x-small"
                    icon="mdi-close"
                    class="mx-0 px-0"
                    color="red"
                    variant="text"
                    @click="removeElementForFootnote(cell.refs[0].uid)"
                  />
                  <v-checkbox
                    v-if="cell.refs.length === 1 && !footnoteMode"
                    v-model="selectedVisitIndexes"
                    :value="index"
                    hide-details
                    multiple
                    :disabled="
                      footnoteMode ||
                      !checkPermission($roles.STUDY_WRITE) ||
                      selectedStudyVersion !== null
                    "
                  />
                  <v-btn
                    v-else-if="!footnoteMode"
                    icon="mdi-delete-outline"
                    color="error"
                    size="x-small"
                    :title="$t('GroupStudyVisits.delete_title')"
                    :disabled="
                      footnoteMode ||
                      !checkPermission($roles.STUDY_WRITE) ||
                      selectedStudyVersion !== null
                    "
                    variant="text"
                    @click="deleteVisitGroup(cell.text)"
                  />
                </div>
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${firstHeaderHeight}px`"
                scope="col"
              />
            </template>
          </tr>
          <tr ref="thirdHeader">
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaDayRow"
                :key="`week-${index}`"
                :style="`top: ${thirdHeaderRowTop}px`"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${thirdHeaderRowTop}px`"
                scope="col"
              />
            </template>
          </tr>
          <tr>
            <th :style="`top: ${fourthHeaderRowTop}px`" scope="col">
              {{ $t('DetailedFlowchart.visit_window') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaWindowRow"
                :key="`window-${index}`"
                :style="`top: ${fourthHeaderRowTop}px`"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${fourthHeaderRowTop}px`"
                scope="col"
              />
            </template>
          </tr>
        </thead>
        <tbody>
          <template v-for="(row, index) in soaRows">
            <tr
              v-if="showSoaRow(index, row)"
              :key="`row-${index}`"
              :class="getSoaRowClasses(row)"
            >
              <td>
                <v-btn
                  v-if="!readOnly && getSoaRowType(row) !== 'activity'"
                  :icon="getDisplayButtonIcon(`row-${index}`)"
                  variant="text"
                  @click="toggleRowState(`row-${index}`)"
                />
              </td>
              <td :class="getSoaFirstCellClasses(row.cells[0])">
                <div class="d-flex align-center justify-start">
                  <v-checkbox
                    v-if="
                      !readOnly &&
                      !footnoteMode &&
                      getSoaRowType(row) === 'activity'
                    "
                    color="primary"
                    hide-details
                    :model-value="
                      studyActivitySelection.findIndex(
                        (cell) => cell.refs[0].uid === row.cells[0].refs[0].uid
                      ) !== -1
                    "
                    :disabled="
                      !checkPermission($roles.STUDY_WRITE) ||
                      selectedStudyVersion !== null
                    "
                    class="flex-grow-0"
                    @update:model-value="
                      (value) => toggleActivitySelection(row, value)
                    "
                  />
                  <v-checkbox
                    v-if="
                      !readOnly &&
                      !footnoteMode &&
                      getSoaRowType(row) === 'subGroup'
                    "
                    color="primary"
                    true-icon="mdi-checkbox-multiple-marked-outline"
                    false-icon="mdi-checkbox-multiple-blank-outline"
                    hide-details
                    :disabled="
                      !checkPermission($roles.STUDY_WRITE) ||
                      selectedStudyVersion !== null
                    "
                    class="flex-grow-0"
                    @update:model-value="
                      (value) => toggleSubgroupActivitiesSelection(row, value)
                    "
                  />
                  <v-badge
                    color="transparent"
                    text-color="secondary"
                    floating
                    :content="
                      row.cells[0].refs.length
                        ? getElementFootnotes(row.cells[0].refs[0].uid)
                        : ''
                    "
                  >
                    {{ row.cells[0].text }}
                  </v-badge>
                  <v-btn
                    v-if="
                      footnoteMode &&
                      !checkIfElementHasFootnote(row.cells[0].refs[0].uid)
                    "
                    size="x-small"
                    icon="mdi-plus"
                    class="mx-0 px-0"
                    variant="text"
                    @click="
                      addElementForFootnote(
                        row.cells[0].refs[0].uid,
                        row.cells[0].refs[0].type
                      )
                    "
                  />
                  <v-btn
                    v-else-if="
                      footnoteMode &&
                      checkIfElementHasFootnote(row.cells[0].refs[0].uid)
                    "
                    size="x-small"
                    icon="mdi-close"
                    class="mx-0 px-0"
                    color="red"
                    variant="text"
                    @click="removeElementForFootnote(row.cells[0].refs[0].uid)"
                  />
                </div>
              </td>
              <td>
                <v-btn
                  v-if="!readOnly"
                  icon
                  :title="$t('DetailedFlowchart.toggle_soa_group_display')"
                  :disabled="
                    footnoteMode ||
                    !checkPermission($roles.STUDY_WRITE) ||
                    selectedStudyVersion !== null
                  "
                  variant="text"
                  @click="toggleLevelDisplay(row)"
                >
                  <v-icon v-if="getLevelDisplayState(row)" color="success">
                    mdi-eye-outline
                  </v-icon>
                  <v-icon v-else> mdi-eye-off-outline </v-icon>
                </v-btn>
              </td>
              <td
                v-if="getSoaRowType(row) !== 'activity'"
                :colspan="row.cells.length - 1"
              />
              <td
                v-for="(visitCell, visitIndex) in soaVisitRow"
                v-else
                :key="`row-${index}-cell-${visitIndex}`"
              >
                <v-row>
                  <v-badge
                    color="transparent"
                    text-color="secondary"
                    :content="
                      row.cells[visitIndex + 1].refs &&
                      row.cells[visitIndex + 1].refs.length
                        ? getElementFootnotes(
                            row.cells[visitIndex + 1].refs[0].uid
                          )
                        : ''
                    "
                    overlap
                  >
                    <v-checkbox
                      v-if="
                        !readOnly &&
                        currentSelectionMatrix[row.cells[0].refs[0].uid][
                          visitCell.refs[0].uid
                        ]
                      "
                      v-model="
                        currentSelectionMatrix[row.cells[0].refs[0].uid][
                          visitCell.refs[0].uid
                        ].value
                      "
                      color="success"
                      :disabled="
                        isCheckboxDisabled(
                          row.cells[0].refs[0].uid,
                          visitCell.refs[0].uid
                        ) ||
                        footnoteMode ||
                        !checkPermission($roles.STUDY_WRITE) ||
                        selectedStudyVersion !== null
                      "
                      hide-details
                      true-icon="mdi-checkbox-marked-circle-outline"
                      false-icon="mdi-checkbox-blank-circle-outline"
                      class="mx-0 px-0"
                      @update:model-value="
                        (value) =>
                          updateSchedule(
                            value,
                            row.cells[0].refs[0].uid,
                            visitCell
                          )
                      "
                    />
                  </v-badge>
                  <v-btn
                    v-if="
                      footnoteMode &&
                      currentSelectionMatrix[row.cells[0].refs[0].uid][
                        visitCell.refs[0].uid
                      ].uid &&
                      !checkIfElementHasFootnote(
                        row.cells[visitIndex + 1].refs[0].uid
                      )
                    "
                    size="x-small"
                    icon="mdi-plus"
                    class="mx-0 px-0"
                    variant="text"
                    @click="
                      addElementForFootnote(
                        row.cells[visitIndex + 1].refs[0].uid,
                        row.cells[visitIndex + 1].refs[0].type
                      )
                    "
                  />
                  <v-btn
                    v-if="
                      footnoteMode &&
                      currentSelectionMatrix[row.cells[0].refs[0].uid][
                        visitCell.refs[0].uid
                      ].uid &&
                      checkIfElementHasFootnote(
                        row.cells[visitIndex + 1].refs[0].uid
                      )
                    "
                    size="x-small"
                    icon="mdi-close"
                    class="mx-0 px-0"
                    color="red"
                    variant="text"
                    @click="
                      removeElementForFootnote(
                        row.cells[visitIndex + 1].refs[0].uid
                      )
                    "
                  />
                </v-row>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <v-expansion-panels class="mt-4">
      <v-expansion-panel>
        <v-expansion-panel-title>
          <div class="text-secondary text-h5">
            <v-icon color="secondary" class="mr-2">
              mdi-map-marker-outline </v-icon
            >SoA Footnotes
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <div
            v-for="footnote of footnotesStore.studyFootnotes"
            :key="footnote.uid"
            class="my-1"
          >
            <v-card flat class="bg-parameterBackground">
              <v-card-text>
                <v-row>
                  <div class="text-secondary mt-2 ml-1">
                    {{ $filters.letteredOrder(footnote.order) }}: &nbsp;
                  </div>
                  <NNParameterHighlighter
                    :name="
                      footnote.footnote
                        ? footnote.footnote.name
                        : footnote.footnote_template.name
                    "
                    class="mt-2"
                  />
                  <v-spacer />
                  <v-btn
                    icon="mdi-pencil-outline"
                    color="primary"
                    :disabled="
                      footnoteMode ||
                      !checkPermission($roles.STUDY_WRITE) ||
                      selectedStudyVersion !== null
                    "
                    variant="text"
                    @click="editStudyFootnote(footnote)"
                  />
                  <v-btn
                    icon="mdi-table-plus"
                    color="primary"
                    :disabled="
                      footnoteMode ||
                      !checkPermission($roles.STUDY_WRITE) ||
                      selectedStudyVersion !== null
                    "
                    variant="text"
                    @click="enableFootnoteMode(footnote)"
                  />
                </v-row>
              </v-card-text>
            </v-card>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
    <StudyActivityScheduleBatchEditForm
      :open="showBatchEditForm"
      :selection="formattedStudyActivitySelection"
      :current-selection-matrix="currentSelectionMatrix"
      @updated="() => loadSoaContent(true)"
      @close="showBatchEditForm = false"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <v-dialog v-model="showCollapsibleGroupForm" persistent max-width="1000px">
      <CollapsibleVisitGroupForm
        :open="showCollapsibleGroupForm"
        :visits="selectedVisits"
        @close="closeCollapsibleVisitGroupForm"
        @created="collapsibleVisitGroupCreated"
      />
    </v-dialog>
    <StudyFootnoteEditForm
      :open="showFootnoteEditForm"
      :study-footnote="selectedFootnote"
      @close="closeEditForm"
      @updated="fetchFootnotes"
      @enable-footnote-mode="enableFootnoteMode"
    />
    <v-dialog
      v-model="showHistory"
      :fullscreen="$globals.historyDialogFullscreen"
      persistent
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :headers="historyHeaders"
        :items="historyItems"
        :items-total="historyItemsTotal"
        :title="historyTitle"
        change-field="action"
        @close="closeHistory"
        @refresh="(options) => getHistoryData(options)"
      />
    </v-dialog>
  </div>
  <v-skeleton-loader
    v-else
    class="mt-6 mx-auto"
    max-width="800px"
    type="table-heading, table-thead, table-tbody"
  />
</template>

<script>
import { computed } from 'vue'
import CollapsibleVisitGroupForm from './CollapsibleVisitGroupForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import exportLoader from '@/utils/exportLoader'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import study from '@/api/study'
import StudyActivityScheduleBatchEditForm from './StudyActivityScheduleBatchEditForm.vue'
import studyEpochs from '@/api/studyEpochs'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import StudyFootnoteEditForm from '@/components/studies/StudyFootnoteEditForm.vue'
import dataFormating from '@/utils/dataFormating'
import _isEmpty from 'lodash/isEmpty'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFootnotesStore } from '@/stores/studies-footnotes'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'

export default {
  components: {
    CollapsibleVisitGroupForm,
    ConfirmDialog,
    HistoryTable,
    StudyActivityScheduleBatchEditForm,
    NNParameterHighlighter,
    StudyFootnoteEditForm,
  },
  inject: ['eventBusEmit'],
  props: {
    readOnly: {
      type: Boolean,
      default: false,
    },
    update: {
      type: Number,
      default: 0,
    },
    redirectFootnote: {
      type: Object,
      default: undefined,
    },
  },
  setup() {
    const accessGuard = useAccessGuard()
    const studiesGeneralStore = useStudiesGeneralStore()
    const footnotesStore = useFootnotesStore()
    const soaContentLoadingStore = useSoaContentLoadingStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      footnotesStore,
      ...accessGuard,
      soaContentLoadingStore,
    }
  },
  data() {
    return {
      currentSelectionMatrix: {},
      expandAllRows: false,
      rowsDisplayState: {},
      firstHeaderHeight: 0,
      secondHeaderHeight: 0,
      thirdHeaderHeight: 0,
      selectedVisitIndexes: [],
      showBatchEditForm: false,
      showCollapsibleGroupForm: false,
      showEditForm: false,
      studyActivities: [],
      studyActivitySchedules: [],
      studyActivitySelection: [],
      studyVisits: [],
      tableHeight: 500,
      activeFootnote: {},
      footnoteMode: false,
      elementsForFootnote: {
        referenced_items: [],
      },
      loadingSoaContent: false,
      selectedFootnote: null,
      showFootnoteEditForm: false,
      showHistory: false,
      footnoteUpdateLoading: false,
      soaGroupsUpdate: false,
      historyHeaders: [
        {
          title: this.$t('DetailedFlowchart.history_object_type'),
          key: 'object_type',
        },
        { title: this.$t('_global.description'), key: 'description' },
        { title: this.$t('_global.modified_by'), key: 'user_initials' },
      ],
      historyItems: [],
      historyItemsTotal: 0,
      soaContent: null,
    }
  },
  computed: {
    soaEpochRow() {
      if (this.soaContent) {
        return this.soaContent.rows[0].cells.slice(1)
      }
      return []
    },
    soaVisitRow() {
      if (this.soaContent) {
        return this.soaContent.rows[1].cells.slice(1)
      }
      return []
    },
    soaDayRow() {
      if (this.soaContent) {
        return this.soaContent.rows[2].cells
      }
      return []
    },
    soaWindowRow() {
      if (this.soaContent) {
        return this.soaContent.rows[3].cells.slice(1)
      }
      return []
    },
    soaRows() {
      if (this.soaContent) {
        return this.soaContent.rows.slice(4)
      }
      return []
    },
    thirdHeaderRowTop() {
      return this.firstHeaderHeight + this.secondHeaderHeight
    },
    fourthHeaderRowTop() {
      return (
        this.firstHeaderHeight +
        this.secondHeaderHeight +
        this.thirdHeaderHeight
      )
    },
    formattedStudyActivitySelection() {
      return this.studyActivitySelection.map((cell) => {
        return {
          study_activity_uid: cell.refs[0].uid,
          activity: { name: cell.text },
        }
      })
    },
    historyTitle() {
      return this.$t('DetailedFlowchart.history_title', {
        study: this.selectedStudy.uid,
      })
    },
    selectedVisits() {
      return this.selectedVisitIndexes.map((cell) => this.soaVisitRow[cell])
    },
  },
  watch: {
    redirectFootnote(value) {
      this.enableFootnoteMode(value)
    },
    update() {
      this.loadSoaContent()
    },
    '$route.params.footnote'(value) {
      if (value && !_isEmpty(value)) {
        this.enableFootnoteMode(value)
      }
    },
  },
  mounted() {
    this.loadSoaContent()
    this.onResize()
    this.fetchFootnotes()
    if (this.$route.params.footnote && !_isEmpty(this.$route.params.footnote)) {
      this.enableFootnoteMode(this.$route.params.footnote)
    }
  },
  updated() {
    if (!this.$refs.firstHeader) {
      return
    }
    this.firstHeaderHeight = this.$refs.firstHeader.clientHeight
    this.secondHeaderHeight = this.$refs.secondHeader.clientHeight
    this.thirdHeaderHeight = this.$refs.thirdHeader.clientHeight
  },
  methods: {
    showSoaRow(index, row) {
      let key = `row-${index}`
      let result = true

      // prettier-ignore
      while (true) { // eslint-disable-line no-constant-condition
        if (
          this.rowsDisplayState[key] &&
          this.rowsDisplayState[key].parent !== undefined &&
          this.rowsDisplayState[key].parent !== null
        ) {
          const parentIndex = this.rowsDisplayState[key].parent
          key = `row-${parentIndex}`
          if (this.rowsDisplayState[key]) {
            // We want to check if parent is an soaGroup or not (not parent === soaGroup)
            if (!this.rowsDisplayState[key].value) {
              result = false
              break
            }
          } else {
            console.log(`Warning: key ${key} not found in displayState!!`)
          }
          continue
        }
        break
      }
      if (row.cells && row.cells.length) {
        if (row.cells[0].style === 'soaGroup') {
          return true
        }
        if (row.cells[0].style === 'group') {
          return result
        }
      }
      return result
    },
    getSoaRowType(row) {
      return row.cells[0].style
    },
    getSoaRowClasses(row) {
      if (row.cells && row.cells.length) {
        if (row.cells[0].style === 'soaGroup') {
          return 'flowchart text-uppercase'
        }
        if (row.cells[0].style === 'group') {
          return 'group'
        }
      }
      return ''
    },
    getSoaFirstCellClasses(cell) {
      if (cell.style === 'soaGroup' || cell.style === 'group') {
        return 'text-strong'
      }
      if (cell.style === 'subGroup') {
        return 'subgroup'
      }
      return 'activity'
    },
    getStudyActivitiesForSoaGroup(soaGroupUid) {
      let groupFound = false
      const result = []
      for (const row of this.soaRows) {
        if (
          row.cells[0].style === 'soaGroup' &&
          row.cells[0].refs[0].uid === soaGroupUid
        ) {
          groupFound = true
        } else if (groupFound) {
          if (row.cells[0].style === 'activity') {
            result.push(row.cells[0])
          } else if (row.cells[0].style === 'soaGroup') {
            break
          }
        }
      }
      return result
    },
    getStudyActivitiesForGroup(groupUid) {
      let groupFound = false
      const result = []
      for (const row of this.soaRows) {
        if (
          row.cells[0].style === 'group' &&
          row.cells[0].refs?.[0]?.uid === groupUid
        ) {
          groupFound = true
        } else if (groupFound) {
          if (row.cells[0].style === 'activity') {
            result.push(row.cells[0])
          } else if (row.cells[0].style === 'group') {
            break
          }
        }
      }
      return result
    },
    getStudyActivitiesForSubgroup(subgroupUid) {
      let subgroupFound = false
      const result = []
      for (const row of this.soaRows) {
        if (
          row.cells[0].style === 'subGroup' &&
          row.cells[0].refs?.[0]?.uid === subgroupUid
        ) {
          subgroupFound = true
        } else if (subgroupFound) {
          if (row.cells[0].style === 'activity') {
            result.push(row.cells[0])
          } else {
            break
          }
        }
      }
      return result
    },
    getElementFootnotes(uid) {
      let footnotesLetters = ''
      this.footnotesStore.studyFootnotes.forEach((footnote) => {
        footnote.referenced_items.forEach((item) => {
          if (item.item_uid === uid) {
            footnotesLetters += dataFormating.letteredOrder(footnote.order)
          } else if (
            uid &&
            typeof uid !== 'string' &&
            uid.includes(item.item_uid)
          ) {
            footnotesLetters += dataFormating.letteredOrder(footnote.order)
          }
        })
      })
      return Array.from(new Set(footnotesLetters.split(''))).toString()
    },
    enableFootnoteMode(footnote) {
      this.activeFootnote = footnote
      this.elementsForFootnote.referenced_items = footnote.referenced_items
      this.footnoteMode = true
    },
    disableFootnoteMode() {
      if (this.$route.params.footnote) {
        this.$router.push({
          name: 'StudyActivities',
          params: { tab: 'footnotes' },
        })
        this.$route.params.footnote = null
      }
      this.activeFootnote = {}
      this.elementsForFootnote.referenced_items = []
      this.footnoteMode = false
      this.fetchFootnotes()
    },
    addElementForFootnote(uid, type) {
      if (typeof uid !== 'string') {
        uid.forEach((u) => {
          this.elementsForFootnote.referenced_items.push({
            item_uid: u,
            item_type: type,
          })
        })
      } else {
        this.elementsForFootnote.referenced_items.push({
          item_uid: uid,
          item_type: type,
        })
      }
    },
    removeFootnote(uid) {
      const indexToRemove = this.elementsForFootnote.referenced_items.findIndex(
        (item) => item.item_uid === uid
      )
      if (indexToRemove !== -1) {
        this.elementsForFootnote.referenced_items.splice(indexToRemove, 1)
      }
    },
    removeElementForFootnote(uid) {
      if (typeof uid !== 'string') {
        uid.forEach((u) => {
          this.removeFootnote(u)
        })
      } else {
        this.removeFootnote(uid)
      }
    },
    saveElementsForFootnote() {
      this.footnoteUpdateLoading = true
      study
        .updateStudyFootnote(
          this.selectedStudy.uid,
          this.activeFootnote.uid,
          this.elementsForFootnote
        )
        .then(() => {
          this.footnoteUpdateLoading = false
          this.disableFootnoteMode()
          this.loadSoaContent(true)
          this.eventBusEmit('notification', {
            msg: this.$t('StudyFootnoteEditForm.update_success'),
          })
        })
    },
    checkIfElementHasFootnote(elUid) {
      if (elUid && typeof elUid === 'string') {
        return this.elementsForFootnote.referenced_items.find(
          (item) => item.item_uid === elUid
        )
      } else if (elUid) {
        return this.elementsForFootnote.referenced_items.find(
          (item) => item.item_uid === elUid[0]
        )
      }
    },
    editStudyFootnote(studyFootnote) {
      this.selectedFootnote = studyFootnote
      this.showFootnoteEditForm = true
    },
    closeEditForm() {
      this.showFootnoteEditForm = false
      this.selectedFootnote = null
    },
    fetchFootnotes() {
      const params = {
        page_number: 1,
        page_size: 0,
        total_count: true,
        studyUid: this.selectedStudy.uid,
      }
      this.footnotesStore.fetchStudyFootnotes(params)
    },
    isCheckboxDisabled(studyActivityUid, studyVisitUid) {
      const state = this.currentSelectionMatrix[studyActivityUid][studyVisitUid]
      return (
        this.readOnly ||
        (state.value && !state.uid) ||
        (!state.value && state.uid !== null)
      )
    },
    getCurrentDisplayValue(rowKey) {
      const currentValue = this.rowsDisplayState[rowKey].value
      if (currentValue === undefined) {
        return false
      }
      return currentValue
    },
    getDisplayButtonIcon(rowKey) {
      return this.getCurrentDisplayValue(rowKey)
        ? 'mdi-chevron-down'
        : 'mdi-chevron-right'
    },
    getLevelDisplayState(row) {
      return !row.hide
    },
    toggleRowState(rowKey) {
      const currentValue = this.getCurrentDisplayValue(rowKey)
      this.rowsDisplayState[rowKey].value = !currentValue
    },
    toggleAllRowState(value) {
      for (const key in this.rowsDisplayState) {
        this.rowsDisplayState[key].value = value
      }
    },
    toggleActivitySelection(row, value) {
      const activityCell = row.cells[0]
      if (value) {
        this.studyActivitySelection.push(activityCell)
      } else {
        for (let i = 0; i < this.studyActivitySelection.length; i++) {
          if (
            this.studyActivitySelection[i].refs[0].uid ===
            activityCell.refs[0].uid
          ) {
            this.studyActivitySelection.splice(i, 1)
            break
          }
        }
      }
    },
    async updateStudyActivity(studyActivityCell, data) {
      await study.updateStudyActivity(
        this.selectedStudy.uid,
        studyActivityCell.refs[0].uid,
        data
      )
    },
    async toggleLevelDisplay(row) {
      const firstCell = row.cells[0]
      let action
      let field

      if (firstCell.style === 'activity') {
        field = 'show_activity_in_protocol_flowchart'
        action = 'updateStudyActivity'
      } else if (firstCell.style === 'subGroup') {
        field = 'show_activity_subgroup_in_protocol_flowchart'
        action = 'updateStudyActivitySubGroup'
      } else if (firstCell.style === 'group') {
        field = 'show_activity_group_in_protocol_flowchart'
        action = 'updateStudyActivityGroup'
      } else if (firstCell.style === 'soaGroup') {
        field = 'show_soa_group_in_protocol_flowchart'
        action = 'updateStudySoaGroup'
      }
      const payload = {}
      payload[field] = row.hide
      await study[action](
        this.selectedStudy.uid,
        firstCell.refs[0].uid,
        payload
      )
      row.hide = !row.hide
    },
    updateGroupedSchedule(value, studyActivityUid, studyVisitCell) {
      if (value) {
        const data = []
        for (const visitRef of studyVisitCell.refs) {
          data.push({
            method: 'POST',
            content: {
              study_activity_uid: studyActivityUid,
              study_visit_uid: visitRef.uid,
            },
          })
        }
        study
          .studyActivityScheduleBatchOperations(this.selectedStudy.uid, data)
          .then((resp) => {
            const scheduleUids = resp.data.map(
              (item) => item.content.study_activity_schedule_uid
            )
            this.currentSelectionMatrix[studyActivityUid][
              studyVisitCell.refs[0].uid
            ].uid = scheduleUids
          })
      } else {
        const data = []
        for (const scheduleUid of this.currentSelectionMatrix[studyActivityUid][
          studyVisitCell.refs[0].uid
        ].uid) {
          data.push({
            method: 'DELETE',
            content: {
              uid: scheduleUid,
            },
          })
        }
        study
          .studyActivityScheduleBatchOperations(this.selectedStudy.uid, data)
          .then(() => {
            this.currentSelectionMatrix[studyActivityUid][
              studyVisitCell.refs[0].uid
            ].uid = null
          })
      }
    },
    updateSchedule(value, studyActivityUid, studyVisitCell) {
      if (studyVisitCell.refs.length > 1) {
        this.updateGroupedSchedule(value, studyActivityUid, studyVisitCell)
        return
      }
      if (value) {
        const data = {
          study_activity_uid: studyActivityUid,
          study_visit_uid: studyVisitCell.refs[0].uid,
        }
        study
          .createStudyActivitySchedule(this.selectedStudy.uid, data)
          .then((resp) => {
            this.currentSelectionMatrix[studyActivityUid][
              studyVisitCell.refs[0].uid
            ].uid = resp.data.study_activity_schedule_uid
          })
      } else {
        const scheduleUid =
          this.currentSelectionMatrix[studyActivityUid][
            studyVisitCell.refs[0].uid
          ].uid
        study
          .deleteStudyActivitySchedule(this.selectedStudy.uid, scheduleUid)
          .then(() => {
            this.currentSelectionMatrix[studyActivityUid][
              studyVisitCell.refs[0].uid
            ].uid = null
          })
      }
    },
    async openBatchEditForm() {
      if (!this.studyActivitySelection.length) {
        this.eventBusEmit('notification', {
          type: 'warning',
          msg: this.$t('DetailedFlowchart.batch_edit_no_selection'),
        })
        return
      }
      const message = this.$t('DetailedFlowchart.batch_edit_warning')
      const options = { type: 'warning' }
      if (!(await this.$refs.confirm.open(message, options))) {
        return
      }
      this.showBatchEditForm = true
    },
    toggleActivitySelectionDisplay(value) {
      if (!this.studyActivitySelection.length) {
        this.eventBusEmit('notification', {
          type: 'warning',
          msg: this.$t('DetailedFlowchart.batch_edit_no_selection'),
        })
        return
      }
      const data = []
      for (const cell of this.studyActivitySelection) {
        data.push({
          method: 'PATCH',
          content: {
            study_activity_uid: cell.refs[0].uid,
            content: {
              show_activity_in_protocol_flowchart: value,
            },
          },
        })
      }
      study
        .studyActivityBatchOperations(this.selectedStudy.uid, data)
        .then(() => {
          this.eventBusEmit('notification', {
            type: 'success',
            msg: this.$t('DetailedFlowchart.update_success'),
          })
          this.loadSoaContent(true)
        })
    },
    toggleSubgroupActivitiesSelection(subgroupRow, value) {
      const activityCells = this.getStudyActivitiesForSubgroup(
        subgroupRow.cells[0].refs?.[0]?.uid
      )
      if (value) {
        this.studyActivitySelection =
          this.studyActivitySelection.concat(activityCells)
      } else {
        for (const activityCell of activityCells) {
          const index = this.studyActivitySelection.findIndex(
            (cell) => cell.refs?.[0]?.uid === activityCell.refs?.[0]?.uid
          )
          this.studyActivitySelection.splice(index, 1)
        }
      }
    },
    redirectTo(value) {
      this.showEditForm = false
      if (['activities', 'footnotes', 'instructions'].indexOf(value) > -1) {
        this.$router.push({
          name: 'StudyActivities',
          params: { study_id: this.selectedStudy.uid, tab: value },
        })
      } else if (['epochs', 'visits'].indexOf(value) > -1) {
        this.$router.push({
          name: 'StudyStructure',
          params: { study_id: this.selectedStudy.uid, tab: value },
        })
      }
    },
    async loadSoaContent(keepDisplayState) {
      this.loadingSoaContent = true
      this.soaContentLoadingStore.changeLoadingState()
      try {
        const resp = await study.getStudyProtocolFlowchart(
          this.selectedStudy.uid,
          false
        )
        this.soaContent = resp.data
      } catch {
        this.loadingSoaContent = false
      }
      let currentSoaGroup
      let currentGroup
      let currentSubGroup

      if (!keepDisplayState) {
        this.rowsDisplayState = {}
        this.expandAllRows = false
      }
      for (const [index, row] of this.soaRows.entries()) {
        const key = `row-${index}`
        if (row.cells && row.cells.length) {
          if (row.cells[0].style === 'soaGroup') {
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = { value: false }
            }
            currentGroup = null
            currentSubGroup = null
            currentSoaGroup = index
          } else if (row.cells[0].style === 'group') {
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = {
                value: false,
                parent: currentSoaGroup,
              }
            }
            currentSubGroup = null
            currentGroup = index
          } else if (row.cells[0].style === 'subGroup') {
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = {
                value: false,
                parent: currentGroup,
              }
            }
            currentSubGroup = index
          } else if (row.cells[0].style === 'activity') {
            const scheduleCells = row.cells.slice(1)
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = {
                value: false,
                parent: currentSubGroup,
              }
            }
            this.currentSelectionMatrix[row.cells[0].refs[0].uid] = {}
            for (const [visitIndex, cell] of this.soaVisitRow.entries()) {
              let props
              if (
                scheduleCells[visitIndex].refs &&
                scheduleCells[visitIndex].refs.length
              ) {
                if (cell.refs.length === 1) {
                  props = {
                    value: true,
                    uid: scheduleCells[visitIndex].refs[0].uid,
                  }
                } else {
                  props = {
                    value: true,
                    uid: scheduleCells[visitIndex].refs.map((ref) => ref.uid),
                  }
                }
              } else {
                props = { value: false, uid: null }
              }
              this.currentSelectionMatrix[row.cells[0].refs[0].uid][
                cell.refs[0].uid
              ] = props
            }
          }
        }
      }
      this.loadingSoaContent = false
      this.soaContentLoadingStore.changeLoadingState()
    },
    onResize() {
      this.tableHeight =
        window.innerHeight -
        this.$refs.tableContainer.getBoundingClientRect().y -
        60
    },
    groupSelectedVisits() {
      const visitUids = this.selectedVisitIndexes.map(
        (cell) => this.soaVisitRow[cell].refs[0].uid
      )
      studyEpochs
        .createCollapsibleVisitGroup(this.selectedStudy.uid, visitUids)
        .then(() => {
          this.collapsibleVisitGroupCreated()
        })
        .catch((err) => {
          if (err.response.status === 400) {
            this.showCollapsibleGroupForm = true
          }
        })
    },
    closeCollapsibleVisitGroupForm() {
      this.showCollapsibleGroupForm = false
    },
    collapsibleVisitGroupCreated() {
      this.eventBusEmit('notification', {
        msg: this.$t('CollapsibleVisitGroupForm.creation_success'),
      })
      this.loadSoaContent(true)
      this.selectedVisitIndexes = []
    },
    async deleteVisitGroup(groupName) {
      const message = this.$t('DetailedFlowchart.confirm_group_deletion', {
        group: groupName,
      })
      const options = { type: 'warning' }
      if (!(await this.$refs.confirm.open(message, options))) {
        return
      }
      await studyEpochs.deleteCollapsibleVisitGroup(
        this.selectedStudy.uid,
        groupName
      )
      this.loadSoaContent(true)
    },
    async getHistoryData(options) {
      const params = {
        total_count: true,
      }
      if (options) {
        params.page_number = options.page ? options.page : 1
        params.page_size = options.itemsPerPage ? options.itemsPerPage : 10
      }
      const resp = await study.getStudySoAHistory(
        this.selectedStudy.uid,
        params
      )
      this.historyItems = resp.data.items
      this.historyItemsTotal = resp.data.total
    },
    async openHistory() {
      await this.getHistoryData()
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
    async downloadCSV() {
      this.soaContentLoadingStore.changeLoadingState()
      try {
        const response = await study.exportStudyDetailedSoa(
          this.selectedStudy.uid
        )
        const filename =
          this.selectedStudy.current_metadata.identification_metadata.study_id +
          ' detailed SoA.csv'
        exportLoader.downloadFile(
          response.data,
          response.headers['content-type'],
          filename
        )
      } finally {
        this.soaContentLoadingStore.changeLoadingState()
      }
    },
    async downloadEXCEL() {
      this.soaContentLoadingStore.changeLoadingState()
      try {
        const response = await study.exportStudyDetailedSoaExcel(
          this.selectedStudy.uid
        )
        const filename =
          this.selectedStudy.current_metadata.identification_metadata.study_id +
          ' detailed SoA.xlsx'
        exportLoader.downloadFile(
          response.data,
          response.headers['content-type'],
          filename
        )
      } finally {
        this.soaContentLoadingStore.changeLoadingState()
      }
    },
    async downloadDOCX() {
      const params = {
        detailed: true,
      }
      this.soaContentLoadingStore.changeLoadingState()
      try {
        const response = await study.getStudyProtocolFlowchartDocx(
          this.selectedStudy.uid,
          params
        )
        const filename =
          this.selectedStudy.current_metadata.identification_metadata.study_id +
          ' detailed SoA.docx'
        exportLoader.downloadFile(
          response.data,
          response.headers['content-type'],
          filename
        )
      } finally {
        this.soaContentLoadingStore.changeLoadingState()
      }
    },
    multipleConsecutiveVisitsSelected() {
      // Check if more than one visit is selected,
      // and that they are in consecutive order without gaps.
      if (this.selectedVisitIndexes.length > 1) {
        const minIndex = this.selectedVisitIndexes.reduce((a, b) =>
          Math.min(a, b)
        )
        const maxIndex = this.selectedVisitIndexes.reduce((a, b) =>
          Math.max(a, b)
        )
        return this.selectedVisitIndexes.length - 1 === maxIndex - minIndex
      }
      return false
    },
  },
}
</script>

<style lang="scss" scoped>
table {
  width: 100%;
  text-align: left;
  border-spacing: 0px;
  border-collapse: collapse;
}
thead {
  background-color: rgb(var(--v-theme-tableGray));
  font-weight: 600;
}
tr {
  padding: 4px;
  &.section {
    background-color: rgb(var(--v-theme-tableGray));
    font-weight: 600;
  }
}
tbody tr {
  border-bottom: 1px solid rgb(var(--v-theme-greyBackground));
}
th {
  vertical-align: bottom;
  background-color: rgb(var(--v-theme-tableGray));
}
th,
td {
  padding: 6px;
  font-size: 14px !important;
}
.sticky-header {
  overflow-y: auto;

  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
  }
}
.flowchart {
  background-color: rgb(var(--v-theme-dfltBackgroundLight1));
}
.group {
  background-color: rgb(var(--v-theme-dfltBackgroundLight2));
}
.subgroup {
  font-weight: 600;
  padding-left: 20px;
}
.activity {
  padding-left: 20px;
}
.text-vertical {
  text-orientation: mixed;
}
.text-strong {
  font-weight: 600;
}
.visitFootnote {
  margin-bottom: 8px;
}
</style>
