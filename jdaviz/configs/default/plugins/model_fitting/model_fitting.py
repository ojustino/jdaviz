import pickle

from glue.core.message import (DataCollectionAddMessage,
                               DataCollectionDeleteMessage)
from traitlets import Bool, List, Dict, Unicode
import astropy.units as u
import astropy.modeling.models as models
from specutils.spectra import Spectrum1D


from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import TemplateMixin
from jdaviz.utils import load_template

from .initializers import initialize_model, model_parameters
from .fitting_backend import fit_model_to_spectrum

__all__ = ['ModelFitting']


@tray_registry('g-model-fitting')
class ModelFitting(TemplateMixin):
    dialog = Bool(False).tag(sync=True)
    template = load_template("model_fitting.vue", __file__).tag(sync=True)
    dc_items = List([]).tag(sync=True)

    save_enabled = Bool(False).tag(sync=True)
    model_savename = Unicode("fitted_model.pkl").tag(sync=True)
    temp_name = Unicode().tag(sync=True)
    temp_model = Unicode().tag(sync=True)
    model_equation = Unicode().tag(sync=True)
    eq_error = Bool(False).tag(sync=True)
    component_models = List([]).tag(sync=True)

    available_models = List(list(model_parameters.keys())).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hub.subscribe(self, DataCollectionAddMessage,
                           handler=self._on_data_updated)
        self.hub.subscribe(self, DataCollectionDeleteMessage,
                          handler=self._on_data_updated)

        self._selected_data = None
        self._spectrum1d = None
        self._fitted_model = None
        self._fitted_spectrum = None
        # Hard coding this for initial testing, want to populate based on
        # selected data
        self._units = {"x": "m", "y": "1E-17 erg/s/cm^2/Angstrom/spaxel"}
        self._y_params = ["amplitude", "amplitude_L", "intercept"]
        self.component_models = []

    def _on_data_updated(self, msg):
       self.dc_items = [x.label for x in self.data_collection]

    def _update_parameters_from_fit(self):
        for m in self.component_models:
            name = m["id"]
            m_fit = self._fitted_model[name]
            temp_params = []
            for i in range(0, len(m_fit.parameters)):
                temp_param = [x for x in m["parameters"] if x["name"] ==
                              m_fit.param_names[i]]
                temp_param[0]["value"] = m_fit.parameters[i]
                temp_params += temp_param
            m["parameters"] = temp_params

    def vue_data_selected(self, event):
        self._selected_data = next((x for x in self.data_collection
                                    if x.label == event))
        self._spectrum1d = self._selected_data.get_object(cls=Spectrum1D)

    def vue_model_selected(self, event):
        # Add the model selected to the list of models
        self.temp_model = event

    def vue_add_model(self, event):
        # Add the selected model and input string ID to the list of models
        new_model = {"id": self.temp_name, "model_type": self.temp_model,
                     "parameters": []}
        for param in model_parameters[new_model["model_type"]]:
            new_model["parameters"].append({"name": param, "value": None,
                                            "unit": self._units["y"] if param in
                                                    self._y_params else self._units["x"],
                                            "fixed": False})
        self.component_models = self.component_models + [new_model]

    def vue_remove_model(self, event):
        self.component_models = [x for x in self.component_models if x["id"] != event]

    def vue_save_model(self, event):
        with open(self.model_savename, 'wb') as f:
            pickle.dump(self._fitted_model, f)

    def vue_equation_changed(self, event):
        # Length is a dummy check to test the infrastructure
        if len(self.model_equation) > 6:
            self.eq_error = True

    def vue_model_fitting(self, *args, **kwargs):
        # This will be where the model fitting code is run
        initialized_models = [initialize_model(x) for x in self.component_models]
        fitted_model, fitted_spectrum = fit_model_to_spectrum(self._spectrum1d,
                                                              initialized_models,
                                                              self.model_equation)
        self._fitted_model = fitted_model
        self._fitted_spectrum = fitted_spectrum
        self.data_collection["Model fit"] = self._fitted_spectrum
        # Update component model parameters with fitted values
        self._update_parameters_from_fit()

        self.save_enabled = True
