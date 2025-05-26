from ..models import VerticalAlignment

class AlignmentUtils:
    @staticmethod
    def get_vertical_alignment_position(alignment: VerticalAlignment, element_height: int, container_height: int) -> int:
        if alignment.align == "center":
            offset = alignment.offset + 0.5
            return (container_height - element_height) * offset
        elif alignment.align == "top":
            return container_height * alignment.offset
        elif alignment.align == "bottom":
            offset = alignment.offset + 1.0
            return container_height * offset - element_height
        
        raise ValueError(f"Invalid alignment: {alignment.align}")