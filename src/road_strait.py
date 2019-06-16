# road_strait.py        
"""
Strait road segment
"""
from homcoord import *


from select_trace import SlTrace
from select_error import SelectError

from block_block import BlockBlock,BlockType
from block_polygon import BlockPolygon
from road_block import RoadBlock,RoadType
   
class RoadStrait(RoadBlock):
    """
    A Strait Part of a road 
    which can be used to construct a road layout
    """
    
            
    def __init__(self,
                 track,
                **kwargs):
        """ Setup Road object
         """
        super().__init__(track, road_type=RoadType.STRAIT, **kwargs)
        tag = self.tag
        tag += "_strait"
        strait = BlockPolygon(container=self.container,
                            tag=tag,
                            position=self.position,
                            width=self.road_width,
                            height=self.road_length,
                            rotation=self.rotation,
                            ctype=BlockType.POLYGON,
                            points=[Pt(0,0), Pt(1,0), Pt(1,1), Pt(0,1)],
                            xkwargs={'fill' : 'black'})
        self.comps.append(strait)

    
    def display(self):
        """ Display thing as a list of components
        """
        self.canvas = self.get_canvas()
        self.canvas.update_idletasks()
        self.canvas.update()
        if not self.visible:
            SlTrace.lg("invisible %s: %s" % (self.road_type, self))
            return              # Skip if invisible
        
        SlTrace.lg("display %s: %s" % (self.road_type, self))
        super().display()
