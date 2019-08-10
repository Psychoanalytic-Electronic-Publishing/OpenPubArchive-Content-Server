var ko = require("knockout");
var $ = require("jquery");
global.jQuery = $; // HACK to make bootstrap work
require("bootstrap");

ko.bindingHandlers.modal = {
	init: function(element, optionsAccessor, allBindingsAccessor, viewModel, bindingContext) {
		var $element = $(element);

		if ($element.attr("tabindex") === undefined) {
			$element.attr("tabindex", -1);
		}

		$element.modal(ko.toJS(optionsAccessor()));

		$element.on("hidden.bs.modal", function() {
			var options = ko.utils.unwrapObservable(optionsAccessor());
			options.show(false);
		});

		$(document).on("keyup", function(e) {
			if (e.which === 27) {
				$element.modal("hide");
			}
		});

		// hide elements inside modal unless we are showing it
		var _showAccessor = showAccessor.bind(optionsAccessor, optionsAccessor);
		ko.bindingHandlers["if"].init(element, _showAccessor, allBindingsAccessor, viewModel, bindingContext);
	},
	update: function(element, optionsAccessor) {
		var _showAccessor = showAccessor.bind(optionsAccessor, optionsAccessor);

		$(element).modal(_showAccessor() ? "show" : "hide");
	}
};

function showAccessor(accessor) {
	var options = ko.utils.unwrapObservable(accessor());
	return ko.utils.unwrapObservable(options.show);
}