<%= include 'HEADER' %>

var Prototype = {
  Version: '<%= PROTOTYPE_VERSION %>',
  emptyFunction: function() {}
}

<%= include 'base.js', 'compat.js', 'string.js' %>
<%= include 'ajax.js', 'dom.js', 'form.js', 'event.js', 'position.js' %>