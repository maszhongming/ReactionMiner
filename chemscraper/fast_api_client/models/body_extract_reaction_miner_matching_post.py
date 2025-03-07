from io import BytesIO
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import File

T = TypeVar("T", bound="BodyExtractReactionMinerMatchingPost")


@_attrs_define
class BodyExtractReactionMinerMatchingPost:
    """
    Attributes:
        pdf (File):
        reaction_miner_json_file (File):
    """

    pdf: File
    reaction_miner_json_file: File
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pdf = self.pdf.to_tuple()

        reaction_miner_json_file = self.reaction_miner_json_file.to_tuple()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pdf": pdf,
                "reaction_miner_json_file": reaction_miner_json_file,
            }
        )

        return field_dict

    def to_multipart(self) -> dict[str, Any]:
        pdf = self.pdf.to_tuple()

        reaction_miner_json_file = self.reaction_miner_json_file.to_tuple()

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = (None, str(prop).encode(), "text/plain")

        field_dict.update(
            {
                "pdf": pdf,
                "reaction_miner_json_file": reaction_miner_json_file,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        pdf = File(payload=BytesIO(d.pop("pdf")))

        reaction_miner_json_file = File(payload=BytesIO(d.pop("reaction_miner_json_file")))

        body_extract_reaction_miner_matching_post = cls(
            pdf=pdf,
            reaction_miner_json_file=reaction_miner_json_file,
        )

        body_extract_reaction_miner_matching_post.additional_properties = d
        return body_extract_reaction_miner_matching_post

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
