// ***************************
// HELPER PAGE DEFAULT CONTENT
// ---------------------------
// Version: 1.40
// Date: 01-10-2022

// -----------------
// Log page handlers
// -----------------

var $ProfileClients = {
    menu                : null,
    selected            : null,

    IsTrace : 0, IsLog : 0,

    item_clients_all    : null,
    left_panel          : null,
    right_panel         : null,
    button_include      : null,
    button_exclude      : null,

    selected_left_item  : null,
    selected_right_item : null,

    items               : new Object(),
    left_side           : null,
    right_side          : null,

    init: function() {
        this.selected_left_item = null;
        this.selected_right_item = null;

        if (this.IsTrace)
            alert('init');

        this.item_clients_all = $("#item-clients-all");
        this.left_panel = $("#profile-clients-left");
        this.right_panel = $("#profile-clients-right");
        this.button_include = $("#profile-clients-include");
        this.button_exclude = $("#profile-clients-exclude");

        this.items = new Object();
        this.left_side = $("#profile-clients-left > ul");
        this.right_side = $("#profile-clients-right > ul");

        this.container = $("#profile-container");

        this.selected = this._get_selected(null);

        if (this.IsLog)
            console.log('$ProfileClients.init:'+this.selected['id'], 'container:'+this.container);

        this.reset();
    },

    reset: function() {
        var self = this;

        if (this.IsTrace)
            alert('reset');

        this.right_side.children().each(function(index) {
            var item = $(this);
            var insert_before = self.getInsertBefore(item, $ProfileClients.left_side);

            if (insert_before != null)
                item.insertBefore(insert_before);
            else
                self.left.append(item);
        });

        self.items = new Object();
    },

    _get_selected: function(ob) {
        if (is_null(ob)) {
            var ob = $("li[class~='selected']", this.container);
            if (is_null(ob))
                ob = $("li", this.container).first();
        }

        var child = ob.children().first();
        var id = child.attr('id');
        var cid = id.split('_')[0];
        var container = $("#"+cid);
        var selected = {'ob':ob, 'child':child, 'id':id, 'cid':cid, 'container':container};

        if (!is_null(this.selected)) {
            this.selected['ob'].removeClass('selected');
            this.selected['container'].hide();
        }
        
        ob.addClass('selected');
        container.show();

        if (this.IsLog)
            console.log('$ProfileClients.selected:', objectKeyValues(selected), 'id:'+id);

        return selected;
    },

    click: function(ob) {
        var id = ob.attr('id');
        var parent = ob.parent();
        this.selected = this._get_selected(parent);
    },

    enable: function() {
        $("#photo_upload").removeClass('disabled');
        //$("#photo_delete").removeClass('disabled');
    },

    disable: function() {
        $("#photo_upload").addClass('disabled');
        //$("#photo_delete").addClass('disabled');
    },

    updatePhoto: function(e) {
        var input = e.target;
        var value = input.files[0];
        var image = $("#photo_image");
        var photo = $("#photo");

        if (this.IsLog)
            console.log('$ProfileClients.updatePhoto, file:', value);

        var reader = new FileReader();
        reader.onloadend = function () { 
            var result = reader.result;
            
            if (this.IsLog)
                console.log('$ProfileClients.updatePhoto, result:', result, 'image:', image.attr('id'));

            if (is_empty(result))
                return;
            
            image.prop("src", result);
            photo.val(result);

            $setUserFormSubmit(0);
        };

        reader.readAsDataURL(value);
    },

    activate: function(checked)
    {
        if (this.IsTrace)
            alert('activate');

        if (checked) {
            this.left_panel.addClass('disabled');
            this.button_include.addClass('disabled');
            this.button_exclude.addClass('disabled');
            this.right_panel.addClass('disabled');
        } else {
            this.left_panel.removeClass('disabled');
            this.button_include.removeClass('disabled');
            this.button_exclude.removeClass('disabled');
            this.right_panel.removeClass('disabled');
        }

        this.item_clients_all.prop('checked', checked);
    },

    _get_item: function(id, container)
    {
        var item = null;

        container.children().each(function(index) {
            if (item != null)
                return;
            else if ($(this).attr('id').split(DEFAULT_HTML_SPLITTER)[1] == id) {
                item = $(this);
            }
        });

        return item;
    },

    getInsertBefore: function(item, container)
    {
        var data = item.attr('data').toLowerCase();
        var insert_before = null;

        if (this.IsTrace)
            alert(data);

        if (is_null(data) || data === undefined || data == '')
            return null;

        container.children().each(function(index) {
            if (insert_before != null)
                return;
            else if ($(this).attr('data').toLowerCase() > data) {
                insert_before = $(this);
            }
        });

        if (this.IsTrace)
            alert('--> before:'+(insert_before != null ? insert_before.attr('data') : '...'));

        return insert_before;
    },

    update: function(data)
    {
        if (is_null(data) || data === undefined || data == '')
            return;

        if (this.IsTrace)
            alert('update');

        var clients = data.split(DEFAULT_HTML_SPLITTER);

        for (var i=0; i < clients.length; i++) {
            var id = clients[i];
            var item = this._get_item(id, this.left_side);
            
            if (is_null(item))
                continue;

            var insert_before = this.getInsertBefore(item, this.right_side);

            if (insert_before != null)
                item.insertBefore(insert_before);
            else
                this.right_side.append(item);

            this.items[id] = 1;
        }

        this.item_clients_all.prop('checked', clients.length > 0 ? 0 : 1);
        this.activate(clients.length > 0 ? false : true);
    },

    setLeft: function(ob, force) {
        if (!force && this.selected_left_item != null)
            this.selected_left_item.removeClass('selected');
       
        ob.addClass('selected');
        this.selected_left_item = ob;
    },

    setRight: function(ob, force) {
        if (!force && this.selected_right_item != null)
            this.selected_right_item.removeClass('selected');
        
        ob.addClass('selected');
        this.selected_right_item = ob;
    },

    getItems: function() {
        var ids = new Array();
        for (var id in this.items) {
            if (this.items[id] == 1)
                ids[ids.length] = id;
        }
        return ids;
    },

    onAddClientProfileItem: function(ob) {
        var item = this.selected_left_item;
        var container = this.right_side;

        if (this.IsTrace)
            alert(left.prop('tagName')+':'+right.prop('tagName'));

        var insert_before = this.getInsertBefore(item, container);

        if (insert_before != null)
            item.insertBefore(insert_before);
        else
            container.append(item);

        item.removeClass('selected');

        var id = item.attr('id').split(DEFAULT_HTML_SPLITTER)[1];
        this.items[id] = 1;

        $setUserFormSubmit(0);

        this.selected_right_item = null;
        var ob = this.getInsertBefore(item, this.left_side);
        if (ob == null)
            return;

        this.setLeft(ob, true);
    },

    onRemoveClientProfileItem: function(ob) {
        var item = this.selected_right_item;
        var container = this.left_side;

        if (this.IsTrace)
            alert(left.prop('tagName')+':'+right.prop('tagName'));

        var insert_before = this.getInsertBefore(item, container);

        if (insert_before != null)
            item.insertBefore(insert_before);
        else
            container.append(item);

        item.removeClass('selected');

        var id = item.attr('id').split(DEFAULT_HTML_SPLITTER)[1];
        this.items[id] = 0;

        $setUserFormSubmit(0);

        this.selected_left_item = null;
        var ob = this.getInsertBefore(item, this.right_side);
        if (ob == null)
            return;

        this.setRight(ob, true);
    }
};

// =========================================================== //

function $setUserFormSubmit(disabled) {
    var container = $("#user-form");
    $("#save", container).prop("disabled", disabled);
}

function $cleanUserForm() {
    var container = $("#user-form");

    $("#login", container).val('').focus();
    $("#password", container).val('');
    $("#family_name", container).val('');
    $("#first_name", container).val('');
    $("#last_name", container).val('');
    $("#post", container).val('');
    $("#email", container).val('');

    var ob = $("#role", container);
    $("option", ob).each(function() {
        var id = $(this).attr('value');
        $(this).prop('selected', int(id) == 0 ? true : false);
    });

    $("#profile-name").html('');

    $("#confirmed", container).prop('checked', 1);
    $("#enabled", container).prop('checked', 1);

    $setUserFormSubmit(0);
}

function $updateUserForm(data) {
    var container = $("#user-form");

    if (is_null(data))
        return;

    $("#login", container).val(data.login);
    $("#password", container).val(data.password);
    $("#family_name", container).val(data.family_name);
    $("#first_name", container).val(data.first_name);
    $("#last_name", container).val(data.last_name);
    $("#post", container).val(data.post);
    $("#email", container).val(data.email);

    var ob = $("#role", container);
    $("option", ob).each(function() {
        var id = $(this).attr('value');
        $(this).prop('selected', data.role == int(id) ? true : false);
    });

    $("#profile-name").html(data.family_name + ' ' + data.first_name + (data.last_name.length>0 ? ' '+data.last_name : ''));

    $("#confirmed", container).prop('checked', data.confirmed);
    $("#enabled", container).prop('checked', data.enabled);

    $setUserFormSubmit(1);
}

function $updateUserPhoto(data) {
    var photo_delete = $("#photo_delete");
    $("#photo_image").prop("src", data);
    if (data.search('person-default') > -1)
        photo_delete.addClass('disabled');
    else
        photo_delete.removeClass('disabled');
}

function $setSettings() {
    var settings = [
        $("#pagesize_bankperso").val(), 
        $("#pagesize_cards").val(), 
        $("#pagesize_persostation").val(), 
        $("#pagesize_config").val(), 
        $("#pagesize_provision").val(), 
        $("#sidebar_collapse").prop('checked')?1:0, 
        $("#use_extra_infopanel").prop('checked')?1:0
    ];
    $("#settings").val(settings.join(':'));

    $setUserFormSubmit(0);
}

function $getSettings(values) {
    if (values) {
        $("#pagesize_bankperso").val(values[0]);
        $("#pagesize_cards").val(values[1]);
        $("#pagesize_persostation").val(values[2]);
        $("#pagesize_config").val(values[3]);
        $("#pagesize_provision").val(values[4]);
        $("#sidebar_collapse").prop('checked', values[5] ? 1 : 0);
        $("#use_extra_infopanel").prop('checked', values[6] ? 1 : 0);
    }
}

function $setPrivileges(values) {
    var privileges = [
        $("#subdivision").val(),
        $("#app_role").val(),
        $("#app_menu").val(),
        $("#base_url").val(),
        $("#app_is_manager").prop('checked')?1:0,
        $("#app_is_author").prop('checked')?1:0,
        $("#app_is_consultant").prop('checked')?1:0
    ];
    $("#privileges").val(privileges.join(':'));

    //alert($("#privileges").val());

    $setUserFormSubmit(0);
}

function $getPrivileges(values) {
    if (values) {
        $("#subdivision").val(values[0]);
        $("#app_role").val(values[1]);
        $("#app_menu").val(values[2]);
        $("#base_url").val(values[3]);
        $("#app_is_manager").prop('checked', values[4] ? 1 : 0);
        $("#app_is_author").prop('checked', values[5] ? 1 : 0);
        $("#app_is_consultant").prop('checked', values[6] ? 1 : 0);
    }
}

// -------------------------
// SubLine Content Generator
// -------------------------

function $updateLog(action, response) {
    var container = null;

    if (IsTrace)
        alert('$updateLog');

    if (IsLog)
        console.log('$updateLog:', action, response);

    // ---------------------------
    // Run Subline/LogPage Handler
    // ---------------------------

    isCallback = true;

    $ActivateInfoData(0);

    $PageController.updateLog(action, response);

    $ActivateInfoData(1);
}

function $updateLogPagination(pages, rows, iter_pages, has_next, has_prev, per_page) {
}

// -------------------------
// TabLine Content Generator
// -------------------------

var TEMPLATE_TABLINE_HEADER = '<th class="column header">VALUE</th>';
var TEMPLATE_TABLINE_ROW = '<tr class="CLASS-LOOP-SELECTED"ID>LINE</tr>';
var TEMPLATE_TABLINE_COLUMN = '<td class="CLASS-CLS-ERROR-READY-SELECTED"EXT>VALUE</td>';
var TEMPLATE_TABLINE_COLUMN_SIMPLE = '<td class="CLASS-SELECTED"EXT>VALUE</td>';

function makeViewLineAttrs(ob, class_name, i) {
    const ID = DEFAULT_HTML_SPLITTER+'ID'+DEFAULT_HTML_SPLITTER;
    var id_template = 'row-'+(class_name || 'tabline')+ID+(i+1).toString();
    if (is_null(ob))
        return ['selected', id_template.replace(/ID/g, '0')];
    var selected = ob['selected'] || '';
    var id = !is_empty(getattr(ob, 'id')) ? id_template.replace(/ID/g, ob['id']) : '';
    return [selected, id];
}

function class_even_odd(i) {
    return i>-1 && i%2==0 ? ' even' : ' odd';
}

function class_selected(selected) {
    return selected ? ' selected' : '';
}

function class_confirm(confirm) {
    return confirm ? ' confirm' : '';
}

function class_error(error) {
    return error ? ' error' : '';
}

function class_ready(ready) {
    return ready ? ' ready' : '';
}

function checkExtraTab(tabs, name) {
    var container = $("#tab-content");
    var ob = $("#data-menu-"+name, container);

    if (!is_null(ob)) {
        if (!is_empty(tabs) && tabs.indexOf(name) > -1)
            ob.removeClass(CSS_INVISIBLE);
        else
            ob.addClass(CSS_INVISIBLE);
    }
}

function makeViewLineRow(id, class_name, i, selected, line) {
    return TEMPLATE_TABLINE_ROW
        .replace(/ID/g, ' id="'+id+'"')
        .replace(/CLASS/g, 'tabline')
        .replace(/-LOOP/g, class_even_odd(i))
        .replace(/-SELECTED/g, class_selected(selected))
        .replace(/LINE/g, line);
}

function makeViewLineColumns(ob, columns, selected, only_columns, column_class_prefix) {
    var column = TEMPLATE_TABLINE_COLUMN;
    var error = getattr(ob, 'Error', 0) ? true : false;
    var ready = getattr(ob, 'Ready', 0) ? true : false;

    var line = '';
    if (is_null(column_class_prefix))
        column_class_prefix = 'log-';

    for(var j=0; j < columns.length; j++) {
        var name = columns[j]['name'];
        var value = (name.length > 0 && (name in ob)) ? ob[name].toString() : '';

        if (only_columns)
            column = only_columns === 'all' || (only_columns === 1 && columns[j]['with_class'])  ? 
                TEMPLATE_TABLINE_COLUMN : TEMPLATE_TABLINE_COLUMN_SIMPLE;

        line += column
            .replace(/CLASS/g, 'column '+column_class_prefix+(name == 'Code' && value.length > 0 ? 
                    value.toLowerCase() : name.toLowerCase()))
            .replace(/-CLS/g, getattr(ob, 'cls', ''))
            .replace(/-ERROR/g, class_error(error))
            .replace(/-READY/g, class_ready(ready))
            .replace(/-SELECTED/g, class_selected(selected))
            .replace(/EXT/g, '')
            .replace(/VALUE/g, value);
    }

    return line;
}

function makeViewNoData(class_name, class_nodata, msg, colspan) {
    return ('<tr id="'+class_name+'-no-data"><tdEXT><div class="'+class_nodata+'">'+msg+'</div></td></tr>')
        .replace(/EXT/g, ' colspan="'+colspan.toString()+'"');
}

function $updateViewData(action, response, props, total, status, path) {
    var flash = $("#flash-section");
    var mid = '';
    var data = response['data'];
    var columns = response['columns'];
    var config = response['config'];

    //alert(action+':'+data.length.toString()+':'+total);

    if (IsLog)
        console.log('$updateViewData, action:'+action, data, props, columns, config, total, status, path);

    function set_text(container, title) {
        var no_data = '<div class="nodata">'+keywords['No data']+'</div>';
        var parent = container.parent();

        $(".row-counting", parent).remove();

        if (data.length == 0) {
            container.html(no_data);
            //container.addClass('p50');
        } else {
            container.text(data);
            container.parent().append(
                '<div class="row-counting">'+(title || 'Всего записей')+': <span id="tab-rows-total">'+total.toString()+
                (!is_empty(status) ? ' '+status : '') +
                '</span></div>'
                );
            container.removeClass('p50');
        }
    }

    function set_table(container, row_class_name, template, only_columns, column_class_prefix, rows_counting, total_html, chunk) {
        var header = TEMPLATE_TABLINE_HEADER;
        var row = TEMPLATE_TABLINE_ROW;
        var column = TEMPLATE_TABLINE_COLUMN;
        var content = '';
        var filename = '';

        content += template || '<table class="view-data" id="tab-view-content" border="1"><thead><tr>';

        for(var i=0; i < columns.length; i++) {
            content += header
                .replace(/VALUE/g, columns[i]['header']);
        }

        content += '</tr></thead><tbody>';

        if (data.length == 0) {
            var no_row_class_name = '';
            var msg = '';

            if (['306','307','308'].indexOf(action) > -1) {
                class_nodata = 'nodataoraccess';
                msg = keywords['No data or access denied'];
            }
            else {
                class_nodata = 'nodata';
                msg = keywords['No data'];
            }

            content += makeViewNoData(row_class_name, class_nodata, msg, columns.length);
        } 
        else {
            if (is_empty(chunk))
                chunk=0;
            for(var i=0; i < data.length; i++) {
                var line = '';
                var ob = data[i];

                if ('exception' in ob && !is_exist(flash)) {
                    flash.append('<div class="flash">'+ob['exception']+'</div>');
                    continue;
                }

                var x = makeViewLineAttrs(ob, row_class_name, i+chunk); 
                var selected = x[0], id = x[1];

                if ('filename' in ob && filename != ob['filename']) {
                    filename = ob['filename'];

                    line = column
                        .replace(/CLASS-CONFIRM-ERROR-READY-SELECTED/g, '')
                        .replace(/VALUE/g, filename)
                        .replace(/EXT/g, ' colspan="'+columns.length.toString()+'"');

                    content += row
                        .replace(/CLASS-LOOP-SELECTED/g, 'log-header')
                        .replace(/ID/g, '')
                        .replace(/LINE/g, line);

                    line = '';
                }

                line += makeViewLineColumns(ob, columns, selected, only_columns, column_class_prefix);
                content += makeViewLineRow(id, row_class_name, i, selected, line);
            }
        }

        content += '</tbody></table>';
        
        if (is_empty(total_html))
            total_html = data.length.toString() + (!is_empty(status) ? ' '+status : '');

        if (is_exist(rows_counting)) {
            ob = rows_counting;
            if (is_exist(ob)) {
                ob.html(total_html);
            }
        } else {
            content += '<div class="row-counting">Всего записей: <span id="tab-rows-total">' + 
                         total_html +
                       '</span></div>';
        }

        if (is_null(container))
            return content;

        if (is_exist(container)) {
            container.html('');
            container.append(content);
        }
    }

    mid = $PageController.updateView(action, {'set_text':set_text, 'set_table':set_table}, response, props, total);

    if (!is_empty(mid))
        $ShowMenu(mid, status, path);

    if (action != default_action)
        selected_menu_action = action;
}

function $updateLineData(action, response, props, total, status, path) {
    var currentfile = response['currentfile'];
    var lines = response['sublines'];
    var config = response['config'];
    var filename = !is_empty(currentfile) ? currentfile[1] : '';

    if (IsTrace)
        alert('$updateLineData:'+action);

    if (IsLog)
        console.log('$updateLineData, action:'+action, response, props, total, status, path);

    $LineSelector.init();

    var data = response['data'];
    var columns = response['columns'];

    selected_menu_action = response['action'];

    // ----------------
    // Refresh LinePage
    // ----------------
    
    $updateViewData(action, response, props, total, status, path);
}

function $updateSublineData(action, response, props, total, status, path) {
    var currentfile = response['currentfile'];
    var sublines = response['sublines'];
    var config = response['config'];
    var filename = !is_empty(currentfile) ? currentfile[1] : '';
    var data = response['data'];
    var columns = response['columns'];

    if (IsTrace)
        alert('$updateSublineData:'+action);

    if (IsLog)
        console.log('$updateSublineData, action:'+action, response, props, total, status, path);

    selected_menu_action = response['action'];

    if (!is_empty(sublines)) {
        subline_refresh(filename);

        // -----------------------
        // Refresh Extra Menu tabs
        // -----------------------

        //checkExtraTab(response['tabs'], 'indigo');

        // -------------------------------------------------
        // Refresh Sublines in order to Init SublineSelector
        // -------------------------------------------------

        if (default_submit_mode != 0)
             $updateViewData(action, response, props, total, status, path);

        $SublineSelector.init();
    }

    // ---------------------------
    // Refresh LogPage or Tablines
    // ---------------------------

    if (selected_menu_action == default_log_action) {
        $updateLog(action, response);
        $TabSelector.reset();
    }
    else
        $updateViewData(selected_menu_action, response, props, total, status, path);
}
