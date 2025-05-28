from ..models import VerticalAlignment, VerticalAlignmentType

class AlignmentUtils:
    @staticmethod
    def get_vertical_alignment_position(alignment: VerticalAlignment, element_height: int, container_height: int) -> int:
        if alignment.align == VerticalAlignmentType.CENTER:
            offset = alignment.offset + 0.5
            return (container_height - element_height) * offset
        elif alignment.align == VerticalAlignmentType.TOP:
            return container_height * alignment.offset
        elif alignment.align == VerticalAlignmentType.BOTTOM:
            # we avoid sending it to the max bottom when the default offset (0.0) is used,
            # doing this, we leave a gap at the bottom 
            offset = alignment.offset + 0.95
            return container_height * offset - element_height
        
        raise ValueError(f"Invalid alignment: {alignment.align}")