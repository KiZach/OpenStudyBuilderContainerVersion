from neomodel import db

from clinical_mdr_api import models
from clinical_mdr_api.listings.query_service import QueryService
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering


class SDTMListingsService:
    def __init__(self):
        self._query_service = QueryService()

    @db.transaction
    def list_tv(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[models.StudyVisitListing]:
        data = self._query_service.get_tv(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(models.StudyVisitListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_ta(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[models.StudyArmListing]:
        data = self._query_service.get_ta(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(models.StudyArmListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_ti(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[models.StudyCriterionListing]:
        data = self._query_service.get_ti(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(models.StudyCriterionListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_ts(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[models.StudySummaryListing]:
        data = self._query_service.get_ts(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(models.StudySummaryListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_te(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[models.StudyElementListing]:
        data = self._query_service.get_te(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(models.StudyElementListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_tdm(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[models.StudyDiseaseMilestoneListing]:
        data = self._query_service.get_tdm(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(models.StudyDiseaseMilestoneListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items
