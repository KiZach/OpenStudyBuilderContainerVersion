from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class TableHeader(BaseModel):
    data: list[str] = Field(
        title="Cell values as text",
    )

    spans: list[int] = Field(
        title="Cell spanning",
        description="1: for normal cells, N: can be merged with following N-1 cells, 0: for cells to hide (merged)",
    )

    def append(self, txt: str, span: int | None = 1):
        """Appends a cell to the header, maintaining .data and .spans, span=0 means to merge with last visible cell"""
        self.data.append(txt)
        self.spans.append(span)

        if span == 0:
            # Find last visible cell and increase spanning of it
            for i in range(len(self.spans) - 2, -1, -1):
                if self.spans[i] > 0:
                    self.spans[i] += 1
                    break

        elif span > 1:
            # Fills cells if span > 1
            for i in range(span - 1):
                self.data.append("")
                self.spans.append(0)
