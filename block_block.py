# block_block.py        

from enum import Enum
import copy
from homcoord import *


from select_trace import SlTrace
from select_error import SelectError

class BlockType(Enum):
    COMPOSITE = 1
    POLYGON = 2
    LINE = 3
    ARC = 4

def tran2matrix(tran):
    """ Display tran's matrix
    :tran: transform
    """
    if tran is None:
        return "None"
    
    return "%s" % tran._m


   
class BlockBlock:
    """
    A BlockBlock is a composite of geometrical things (currently 2-dimensional) 
    which can be used to construct hierarchical graphical objects
    Object properties are expressed in relation to the containing object (container),
    if one, else in relation to the canvas (cv_width, cv_height)  The values of
    cv_width, cv_height are needed because canvas.wininfo are not always available.
    
    Internal coordinate system is Cartesian:
         x to left, y to up
         x=0: right side, y=0: botom
    
      position    Pt()  within container
      width       0.to 1 of container width
      height      0. to 1 of container height
      rotation    rotation (degrees counter clockwise) relative to container
                  0 = strait up
      velocity    velocity: x,y / second
    internal:
      base_xtran - homogenous transform when needed
    When a BlockBlock moves/rotates The components move/rotate accordingly
    """
    id = 0


    @classmethod
    def get_xtran(self, comp):
        """ Get transformation of comp + containers
        :comp: componenet whos transform is desired
        :returns: transform from top to comp
        """
        comps = [comp]
        while comp.container is not None:
            comps.insert(0, comp.container)
            comp = comp.container
        
        xtran = None
        for comp in comps:
            xtran_next = comp.base_xtran()
            if xtran_next is not None:
                if xtran is None:
                    xtran =xtran_next
                else:
                    xtran = xtran.compose(xtran_next)
        return xtran

            
    def __init__(self,
                 canvas=None,
                 cv_width=None,
                 cv_height=None,
                 container=None,
                 ctype=BlockType.COMPOSITE,
                 position=None,
                 width=None, height=None,
                 rotation=None,
                 velocity=None,
                 visible=True,
                 tag="",
                 xkwargs=None):
        """ Setup object
        :canvas: optional canvas argument - provides Canvas if no container
        :cv_width: optional canvas width
        :cv_height: optional canvas height
        :container: containing object(BlockBlock), default: this is the base object
        :ctype: container type defalut:COMPOSITE
        :width: width as a fraction of container's width dimensions'
                e.g. 1,1 with container==None ==> block is whole canvas
                If container is None
                    width = width * self.cv_width
        :height" height as a fraction of container's height
        :position: position of lower left corner(x=0, y=0) relative to container's position (x=0, y=0)
        :rotation:  rotation relative to container's rotation
        :velocity:  velocity relative to container's velocity
        :visible:   visible iff container's visible default: seen
        :points:    points, used for this component
        :tag:    Optional identifier  default: ""
        :xkwargs:   optional canvas operation args (dictionary to avoid name
                                                    collisions)
        """
        BlockBlock.id += 1
        self.id = BlockBlock.id
        self.tag = tag
        self.canvas = canvas
        if cv_width is not None:
            self.cv_width = cv_width
        if cv_height is not None:
            self.cv_height = cv_height
        self.canvas = canvas     
        self.container = container
        SlTrace.lg("\nBlockBlock[%d]:%s %s %s container: %s" % (self.id, tag, ctype, self, container))
        SlTrace.lg("tag_list: %s" % self.get_tag_list())    
        self.comps = []     # List of components
        self.ctype = ctype

        if width is not None or height is not None: # Any scaling ?
            if width is None:
                width = 1.          # Whole continer
            if height is None:
                height = 1.          # Whole continer
        
        if container is None:               # Top of heap ?
            if width is not None:               # Any scaling
                width *= self.get_cv_width()          # Scale width to canvas
                height *= self.get_cv_height()            
                        
        self.position = position
        self.width = width
        self.height = height
        self.velocity = velocity
        self.rotation = rotation        
        self.visible = visible
        self.xkwargs = xkwargs
        ###self.xtran = self.base_xtran()     # Setup this component's translation matrix
        ###self.xtran = BlockBlock.get_xtran(self)
 
    def get_tag_list(self):
        """ List of tags from top container to this component
        """
        tag_list = self.tag
        comp = self
        while comp.container is not None:
            comp = comp.container
            tag_list = comp.tag + ":" + tag_list
        return tag_list


    def get_top_container(self):
        """ Get top containing block
        :returns: top container, self if no container
        """
        top = comp = self
        while comp.container is not None:
            top = comp = comp.container
        return top


    def get_relative_points(self, points=None):
        """ Get points based on current block position
        :points: base point/points to translate
                defajlt: self.points
        :returns: list of translated points
                e.g. if default gives points as transformed
                by base transform
        """
        if points is None:
            points = self.points
        if not isinstance(points, list):
            points = [points] 
        xtran = self.base_xtran()
        if xtran is None:
            return points
        
        pts = []
        position = Pt(0,0) if self.position is None else self.position
        rtran = Xrotate(radians(self.rotation))
        stran = Xscale(self.width, self.height)
        ttran = Xlate(position.x, position.y)
        xtran = rtran * stran * ttran
        itran = xtran.inverse()
        
        for pt in points:
            pt_x = xtran.apply(pt)
            pts.append(pt_x)
        return pts


    def get_relative_point(self, pt):
        """ get single point relative to current position
        :pt: current relative point
        :returns: point in container's reference
        """
        pts = self.get_relative_points(pt)
        return pts[0]
    
    
    
    def get_canvas(self):
        """ Get our canvas
        :returns: canvas, None if no canvas or top
        """
        if self.canvas is not None:
            return self.canvas
        
        top = self.get_top_container()
        return top.canvas
    
    
    def get_cv_height(self):
        """ Return canvas height (or projected height)
        """
        if hasattr(self, "cv_height") and self.cv_height is not None:
            return self.cv_height
        
        top = self.get_top_container()
        return top.cv_height
    
    
    def get_cv_width(self):
        """ Return canvas width (or projected width)
        """
        if hasattr(self, "cv_height") and self.cv_width is not None:
            return self.cv_width
        
        top = self.get_top_container()
        return top.cv_width

    def has_canvas(self):
        """ Determine if this object has a canvas
        """
        if self.canvas is not None:
            return True
        
        top = self.get_top_container()
        if hasattr(top, "canvas"):
            return True
        
        return False
               
    def base_xtran(self):
        """ Create this component's contribution
        to the translation:
        Find local scale = canvas size * scale_top * scale_next *...* scale_next
        offset(x,y) = scale * position(x,y)
        if no container (container is None)
           1. scale to canvas dimensions
               sx = width*cv_width
               sy = height*cv_height
           2. rotate by rotation
           3. translate
               offset_x = offset(x)
               offset_y = offset(y)
        else
           1. scale relative (fractions 0-1)
               sx = width
               sy = height
           2. rotate by rotation(cvt deg to radian)
           3. translate to position
               offset_x = offset(x)
               offset_y = offset(y)
        Omit transformations, having no effect e.g.
                translate(0,0)
                rotation(0)
                scale(1,1)
        Result:
            self.xtran is None if no translation
            self.xtran == translation for this component (before sub parts such as points)
        """
        SlTrace.lg("\nbase_xtran: %s" % self)
        width = self.width
        height = self.height
        position = self.position

        comp = self
        comps = []                  # Scale through all containers
        while comp.container is not None:
            comps.insert(0, comp.container)
            comp = comp.container
        
        scale_x = 1.
        scale_y = 1.
        for comp in comps:
            if comp.width is not None:
                scale_x *= comp.width
            if comp.height is not None:
                scale_y *= comp.height
        
            
        xtran = None                # Changed if any scaling
        if self.rotation is not None:
            xfr = Xrotate(radians(self.rotation))
            SlTrace.lg("xfr=%s" % xfr)
            if xtran is None:
                xtran = xfr                                 # Start with this transform
            else:
                self.xtran = xtran.compose(xfr)        # Add this transform
        if width is not None:       # one or none
            xfs = Xscale(width, height)                       # Scale by comp size
            SlTrace.lg("xfs=%s" % xfs)
            if xtran is None:
                xtran = xfs                            # Start with this transform
            else:
                xtran = xtran.compose(xfs)        # Add this transform
        if position is not None:
            SlTrace.lg("scale_x=%5.2g scale_y=%5.2g" % (scale_x, scale_y))
            xft = Xlate(scale_x*self.position.x, scale_y*self.position.y)    # Move to origin
            if xtran is None:
                xtran = xft
            else:
                xtran = xtran.compose(xft)
        SlTrace.lg("xtran=%s" % xtran)
        return xtran
    
        
    def update_xtran(self):
        """ Create this component's contribution
        to the translation:
          0. get transform for container
          1. translate to origin within container(if one)
          2. scale by size
          3. rotate by rotation(cvt deg to radian)
          4. translate to position within container(if one)
        Omit transformations, having no effect e.g.
                translate(0,0)
                rotation(0)
                scale(1,1)
        Result:
            self.xtran is None if no translation
            self.xtran == translation for this component (before sub parts such as points)
        """
        self.xtran = self.get_xtran(self.container)    # Initialize container's transform
        if self.width is not None or self.height is not None:
            if self.width is None:
                self.width = 1.     # Default scale to full
            if self.height is None:
                self.height = 1.
            xfs = Xscale(self.width, self.height)                       # Scale by comp size
            SlTrace.lg("xfs=%s" % xfs)
            if self.xtran is None:
                self.xtran = xfs                            # Start with this transform
            else:
                self.xtran = self.xtran.compose(xfs)        # Add this transform
        if self.rotation is not None:
            xfr = Xrotate(radians(self.rotation))
            SlTrace.lg("xfr=%s" % xfr)
            if self.xtran is None:
                self.xtran = xfr                                 # Start with this transform
            else:
                self.xtran = self.xtran.compose(xfr)        # Add this transform
        if self.position is not None:
            xft = Xlate(self.position.x, self.position.y)    # Move to origin
            if self.xtran is not None:
                self.xtran = self.xtran.compose(xft)
        SlTrace.lg("xtran=%s" % self.xtran)
    
    def add_components(self, comps):
        """ Add component/list of components
        :comps: one or list of components
        """
        if not isinstance(comps, list):
            comps = [comps]
        for comp in comps:
            self.comps.append(comp)

    
    def display(self):
        """ Display thing as a list of components
        """
        SlTrace.lg("tag_list: %s" % self.get_tag_list())
        self.task_update()    
        if not self.visible:
            SlTrace.lg("invisible %s: %s" % (self.ctype, self))
            return              # Skip if invisible
        
        SlTrace.lg("display %s: %s" % (self.ctype, self))
        if self.ctype == BlockType.COMPOSITE:
            for comp in self.comps:
                comp.display()
        else:
            self.display_base()
        self.task_update()    


    def task_update(self):
        """ Up Tkinter tasks so display can be seen as soon as possible
        """
        canvas = self.get_canvas()
        if canvas is not None:
            canvas.update_idletasks()
            canvas.update()


    def display_base(self):
        """ display base type
        """
        if self.ctype == BlockType.POLYGON:
            self.display_polygon()
        else:
            raise SelectError("Unsupported base type %s" % self.ctype)

 
    def display_polygon(self):
        """ Display polygon
        The polygon consists of a list of points
        whose position must be transformed though
        the coordinates of each of the enclosing
        components.
        Each of the components, upon creation,
        stored a translation matrix in .xtran.
        
        We will create a single translation matix
        by composing the individual translation
        matrixes from the top container.
        """
        SlTrace.lg("\ndisplay_polygon points[%s]=%s" % (self.tag, self.points))
        SlTrace.lg("tag_list: %s" % self.get_tag_list())    
        
        if self.width is not None:
            SlTrace.lg("width=%.1g" % self.width)
        if self.height is not None:
            SlTrace.lg("height=%.1g" % self.height)
        if self.position is not None:
            SlTrace.lg("position=%s" % self.position)
        if self.rotation is not None:
            SlTrace.lg("rotation=%.1fdeg" % self.rotation)
        comp = self
        comps = [comp]
        while comp.container is not None:
            comps.insert(0, comp.container)
            comp = comp.container
        xtran = None
        for cp in comps:
            base_xtran = cp.base_xtran()
            SlTrace.lg("cp: %s     base_xtran: %s" % (cp.get_tag_list(), base_xtran))
            if base_xtran is not None:
                if xtran is not None:
                    xtran = xtran.compose(base_xtran)
                else:
                    xtran = base_xtran
            SlTrace.lg("xtran=%s" % xtran)
        SlTrace.lg("_m:%s" % tran2matrix(xtran))
        pts = []     # x1,y1, x2,y2, list
        for point in self.points:
            pt = xtran.apply(point)
            pts.append(pt)
        SlTrace.lg("create_polygon(points:%s" % (pts))
        coords = self.pts2coords(pts)
        SlTrace.lg("create_polygon(coords:%s, kwargs=%s" % (coords, self.xkwargs))
        canvas = self.get_canvas()
        canvas.create_polygon(coords, **self.xkwargs)


    def tran_points_to_coords(self, points, comp):
        """ Translate points from component to  coordinates
        for Canvas create_poligon
        :points: list of position coordinates
        :comp: expanded position attributes
        """
        pts = []
        for point in self.points:
            pt = self.point_tran(point, comp)
            pts.append(pt)
            
        coords = []
        for pt in pts:
            coords.append(pt[0])
            coords.append(pt[1])


    def tran_point(self, point, comp):
        """ Translate point based on component hierachy
        :point: point in inner most component
        :comp: general component
        """


    def add_to_rot(self, comp):
        """ Adjust possition by relative position of component
        :comp: component containing relative information
        """
        pass        # TBD


    def add_to_vel(self, comp):
        """ Adjust velocity by relative position of component
        :comp: component containing relative information
        """
        pass        # TBD
   
     
    def get_components(self):
        """ Get list of components
        """
        return self.comps

    def move(self, delta, display=True):
        """ Move thing, and all components.
        :delta: change in position
        :display: display updated thing default: True
        """
        for comp in self.get_components():
            comp.move(delta)
        if display:
            comp.display()
    
    
    def coords2pts(self, coords):
        """ Convert Canvas coordinate list to list of
        homcord Pt()
        :coords: list of x1,y1,...xn,yn coordinates
        :returns: list of homcoord Pt()
        """
        canvas = self.get_canvas()
        cv_height = self.get_cv_height()
        height = canvas.winfo_height()
        points = []
        for x,y in coords:
            y = cv_height - y      # down to up
            pt = Pt(x,y) 
            points.append(pt)
        return points
    
    
    def pts2coords(self, pts):
        """ Convert homcoord points to Canvas coordinate list
        :pts: list of homcoord Pt()
        :returns: list of x1,y1,....xn,yn coordinates
        """
        cv_height = self.get_cv_height()
        coords = []
        for pt in pts:
            x, y = pt.xy
            y = cv_height - y 
            coords.extend([x,y])
        return coords
    