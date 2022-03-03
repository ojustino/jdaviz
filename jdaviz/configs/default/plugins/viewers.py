from glue_jupyter.bqplot.profile import BqplotProfileView
from glue_jupyter.bqplot.image import BqplotImageView
from glue_jupyter.table import TableViewer

from jdaviz.components.toolbar_nested import NestedJupyterToolbar
from jdaviz.core.registries import viewer_registry


__all__ = ['JdavizViewerMixin']

viewer_registry.add("g-profile-viewer", label="Profile 1D", cls=BqplotProfileView)
viewer_registry.add("g-image-viewer", label="Image 2D", cls=BqplotImageView)
viewer_registry.add("g-table-viewer", label="Table", cls=TableViewer)


class JdavizViewerMixin:
    toolbar_nested = None
    tools_nested = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _initialize_toolbar_nested(self):
        # would be nice to call this from __init__,
        # but because of inheritance order that isn't simple
        self.toolbar_nested = NestedJupyterToolbar(self, self.tools_nested)

    @property
    def jdaviz_app(self):
        """The Jdaviz application tied to the viewer."""
        return self.session.jdaviz_app

    @property
    def jdaviz_helper(self):
        """The Jdaviz configuration helper tied to the viewer."""
        return self.jdaviz_app._jdaviz_helper

    @property
    def reference_id(self):
        # TODO: this should probably be stored instead of this hideously hacky loop
        for id in self.jdaviz_app.get_viewer_ids():
            if self.jdaviz_app.get_viewer_by_id(id) == self:
                return id
        return None
