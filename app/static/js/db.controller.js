// ************************
// FRONNTSIDE DB CONTROLLER
// ------------------------
// Version: 2.00
// Date: 12-11-2021

var current_order_type = -1;            // Order type (otype) code value
var current_order_code = '';            // Current Order code value: C-000-0000

var LOG_SORT = new Array('', 'TOTAL-DESC', 'TOTAL-ASC', 'DATE-DESC', 'DATE-ASC', 'CUSTOM-CODE-DESC', 'CUSTOM-CODE-ASC');

var current_sort = 0;                   // Sorting index
var page_sort_title = '';               // Sorting title tag value

var current_line = null;                // Current (selected on Data section) line row
var current_subline = null;             // Current (selected on LogData section) subline row
var current_tabline = null;             // Current (selected on TabData section) line row

var current_row_id = null;              // ID of current (selected on Data section) row

var selected_data_menu_id = '';         // Selected Data menu item (Parameters/Products)
var selected_data_menu = null;          // Selected Data menu Object
var selected_dropdown = null;           // Selected Dropdown menu Object

var is_search_activated = false;        // Search is active
var is_search_focused = false;          // Search input in focus

// -------------------
// TabLines controller
// -------------------

var tablines = new Object();            // Tablines entities
var selector = new Object();            // Pointer to current (selected) object
var tabs= 0;                            // Counter of entites
var controllers = new Array();          // Controllers list
var active_controller = 0;              // Active controller index

var search_context = '';                // Current search context value

// ****************************************************

var default_row_item = {'num':0, 'id':null, 'ob':null};
var selected_row = 
{
    'admin'         : new Object(),
    'admlogs'       : new Object(),
    'configs'       : new Object(),
    'param'         : new Object(),
    'divisions'     : new Object(),
    'nodes'         : new Object(),
    'messagetypes'  : new Object(),
    'binds'         : new Object(),
    'activities'    : new Object(),
    'reliabilities' : new Object(),
    'capacities'    : new Object(),
    'speeds'        : new Object(),
    'history'       : new Object(),

//  ---  Default Tab Line ---

    'tabline'       : new Object(),
};

function SelectedReset() {
    for(var key in selected_row) {
        selected_row[key] = new Object();
        for(var item in default_row_item)
            selected_row[key][item] = default_row_item[item];
    }
}

function SelectedSetItem(key, item, ob) {
    if (IsLog)
        console.log('SelectedSetItem.key:['+key+'], item:['+item+'], id:['+(ob && ob.attr('id'))+']');

    if (key in selected_row) {
        selected_row[key][item] = ob;
        if (item == 'ob')
            selected_row[key]['id'] = !is_null(ob) ? $_get_item_id(ob, -1) : null;
    }
}

function SelectedGetItem(key, item) {
    return !is_null(selected_row[key]) && (item in selected_row[key]) ? selected_row[key][item] : null;
}

// =====================
// Page Controller Timer
// =====================

var timer = null;

function sleep(callback, timeout) {
    timer = setTimeout(callback, timeout);
}

function clear_timeout() {
    if (!is_null(timer)) {
        clearTimeout(timer);
        timer = null;
    }
}

// =======================
// Selected Items Handlers
// =======================

var $ActiveSelector = {
/***
 * Auxiliary class to manage selection between Subline and Tabline areas.
 * Used for instance by `configurator.js` only.
 */

    selector : null,

    release: function() {
        if (is_null(this.selector))
            return;

        this.selector.release();
    },

    reset: function(ob) {
        this.selector = ob;

        if (IsLog)
            console.log('$ActiveSelector.reset:'+this.selector.alias);
    },

    is_movable: function() {
        if (is_null(this.selector))
            return;

        return this.selector.is_movable();
    },

    get_current: function() {
        if (is_null(this.selector))
            return;

        return this.selector.get_current();
    },

    onRefresh: function(ob) {
        if (is_null(this.selector))
            return;

        return this.selector.onRefresh(ob);
    },

    onProgress: function(ob) {
        if (is_null(this.selector))
            return;

        return this.selector.onProgress(ob);
    },

    up: function() {
        if (is_null(this.selector))
            return;

        return this.selector.up();
    },
    
    down: function() {
        if (is_null(this.selector))
            return;

        return this.selector.down();
    },

    home: function() {
        if (is_null(this.selector))
            return;

        return this.selector.home();
    },
    
    pgup: function() {
        if (is_null(this.selector))
            return;

        return this.selector.pgup();
    },
    
    pgdown: function() {
        if (is_null(this.selector))
            return;

        return this.selector.pgdown();
    },
    
    end: function() {
        if (is_null(this.selector))
            return;

        return this.selector.end();
    }
};

var $LineSelector = {
/***
 * Basic class to manage selection of Line area: moving inside control (up|down|pgup|pgdown|begin|end).
 * 
 * Controls:
 *    $("#position"): pointer of current state inside area: page|pages|per_page|line
 * 
 * Protected methods:
 *    _find:
 *    _move:
 *    _refresh:     push $onToggleSelectedClass submit action
 * 
 * Public methods:
 *    init:
 *    reset:
 *    set_current:  
 *    set_position: 
 *    get_id:
 *    get_current:
 *    onRefresh:
 * 
 */
    container : null,

    // ===================
    // Line Selector Class
    // ===================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ----------------------------------------------------------
    // Current page (position): [0]:page, [1]:pages, [2]:per_page
    // ----------------------------------------------------------

    position  : new Array(),
    current   : null,
    oid       : '',
    number    : 0,

    page      : 0,
    pages     : 0,
    per_page  : 0,
    line      : 0,

    is_top    : false,
    is_bottom : false,

    is_end_of_data : false,

    init: function() {
        this.container = $("#line-content");
        if (!is_exist(this.container)) {
            this.container = null;
        }

        // XXX check if exists #position
        ob = $("#position");
        if (is_exist(ob)) {
            $("#position").val().split(':').forEach(function(x) { this.push(parseInt(x) || 0); }, this.position);

            this.page = this.position[0];
            this.pages = this.position[1];
            this.per_page = this.position[2];
            this.line = this.position[3];
        }

        if (this.IsTrace)
            alert('$LineSelector.init:'+joinToPrint(this.position));

        this.current = null;
        this.oid = '';
        this.number = 0;

        var ob = null;

        if (!is_null(this.container)) {
            ob = $("tr[class~='selected']", this.container);
            $onToggleSelectedClass(LINE, ob, 'add', null);
        }

        this.set_current(ob);

        this.reset();
    },

    reset: function() {
        this.is_top = this.is_bottom = this.is_end_of_data = false;
    },

    get_id: function() {
        return !is_null(this.current) ? $_get_item_id(this.current, -1) : null;
    },

    get_current: function() {
        return this.current;
    },

    set_current: function(ob) {
        if (is_null(ob))
            return;

        this.current = ob;
        this.oid = ob.attr('id');
        this.number = parseInt($_get_item_id(ob, -1));

        this.set_position(this.page, this.number);

        if (this.IsTrace)
            alert('$LineSelector.set_current.number:'+this.number);
    },

    set_position: function(page, line) {
        $("#position").val(page+':::'+line);
    },

    onReset: function() {
        this.reset();
        return this._refresh(0);
    },

    onRefresh: function(ob) {
        if (is_null(ob)) {
            SelectedSetItem(LINE, 'ob', null);
            ob = this.get_current();
        }

        this._remove();
        this.set_current(ob);
        return this._refresh(0);
    },

    onFormSubmit: function() {
        this.set_position(1, 1);
    },

    get_items: function() {
        if (is_null(this.container))
            return;

        return this.container.find(".line");
    },

    getSelectedItems: function(position) {
        if (is_null(this.container))
            return;

        var items = new Array();

        this.container.find(".line").each(function(index, x) {
            if (this.IsTrace)
                alert('$LineSelector.getSelectedItems:'+$(x).attr('id')+':'+parseInt($_get_item_id($(x), -1)));

            items.push(is_null(position) ? $(x) : parseInt($_get_item_id($(x), position)));
        });

        return items;
    },

    _remove: function() {
        var ob = this.current;
        if (!is_null(ob)) {
            $onToggleSelectedClass(LINE, ob, 'remove', null);
        }

        if (this.IsLog)
            console.log('$LineSelector._remove:', this.oid, ob, this.number);
    },

    _find: function(num) {
        if (is_null(this.container))
            return;

        var ob = null;

        this.container.find(".line").each(function(index, x) {
            if (this.IsTrace)
                alert('getSelectedItems._find:'+$(x).attr('id')+':'+parseInt($_get_item_id($(x), -1)));
            if (parseInt($_get_item_id($(x), -1)) == num)
                ob = $(x);
        });

        if (this.IsTrace)
            alert('getSelectedItems._find:'+'found:'+(ob ? ob.attr('id') : 'null'));

        return ob;
    },

    _refresh: function(new_page) {
        if (is_null(this.container))
            return;

        var exit = false;
        var page, line;

        if (this.IsLog)
            console.log('$LineSelector._refresh:'+this.number+':'+this.is_top+':'+this.is_bottom+':'+new_page);

        // --------------------
        // Refresh current page
        // --------------------

        if (new_page == 0 && !(this.is_top || this.is_bottom || this.is_end_of_data)) {
            $onToggleSelectedClass(LINE, this.current, 'add', null);
            exit = true;
        }

        // ---------------
        // Open a new page
        // ---------------

        else {        
            if (new_page == 1) {
                page = new_page;
                line = 1;
            }
            else if (new_page > 0) {
                page = new_page;
                line = this.number;
            }
            else if (this.is_top) {
                page = this.page - 1;
                line = this.per_page;
            }
            else if (this.is_bottom) {
                page = this.page + 1;
                line = 1;
            }
            else
                return true;

            this.set_position(page, line);

            MakeFilterSubmit(9, page);

            exit = true;
        }

        return exit;
    },

    _move: function(direction) {
        var ob = null;
        var is_found = false;
        var num;

        // ------------------------
        // Move inside current page
        // ------------------------

        if ((direction > 0 && this.number < this.per_page) || (direction < 0 && this.number > 1)) {
            num = this.number + (direction > 0 ? 1 : -1);
            ob = this._find(num);
            if (!is_null(ob)) {
                this.current = ob;
                this.number = num;
                //this.set_current(ob);
                is_found = true;
            }
        }

        this.reset();

        if (!is_found) {
            this.is_end_of_data = (
                (direction < 0 && this.page == 1) || 
                (direction > 0 && this.page == this.pages)
                ) ? true : false;

            this.is_top = (direction < 0 && !this.is_end_of_data) ? true : false;
            this.is_bottom = (direction > 0 && !this.is_end_of_data) ? true : false;
        }

        if (this.IsTrace)
            alert('getSelectedItems._move:'+'move:'+this.number+':'+this.is_top+':'+this.is_bottom);

        return is_found || this.is_top || this.is_bottom;
    },

    home: function() {
        return this._refresh(1);
    },

    up: function() {
        return this._move(-1) === true ? this._refresh(0) : false;
    },

    down: function() {
        return this._move(1) === true ? this._refresh(0) : false;
    },

    pgup: function() {
        return this.page > 1 ? this._refresh(this.page-1) : false;
    },

    pgdown: function() {
        return this.page < this.pages ? this._refresh(this.page+1) : false;
    },

    end: function() {
        return this._refresh(this.pages);
    }
};

var $SublineSelector = {
    container : null,

    // ======================
    // Subline Selector Class
    // ======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ----------------
    // Config Object ID
    // ----------------

    alias     : '',         // Subline Object name
    mode      : '',

    current   : null,
    oid       : '',
    number    : 0,

    page      : 0,
    pages     : 0,
    per_page  : 0,
    line      : 0,

    is_top    : false,
    is_bottom : false,

    is_end_of_data : false,

    init: function() {
        this.container = $("#subline-content");
        if (!is_exist(this.container)) {
            this.container = null;
            this.is_end_of_data = true;
        }

        if (this.IsLog)
            console.log('$SublineSelector.init');

        this.alias = SUBLINE;

        this.page = 1;
        this.pages = 1;
        this.line = 1;

        this.current = null;
        this.oid = '';
        this.number = 0;

        if (is_empty(this.alias))
            return;

        this.release();

        var ob = null;

        if (!is_null(this.container)) {
            ob = $("tr[class~='selected']", this.container);
            SelectedSetItem(this.alias, 'ob', ob, null);
        }

        this.set_current(ob);

        this.reset();
    },

    release: function() {
        this.current = null;
        this.oid = '';
        this.number = 0;

        SelectedSetItem(this.alias, 'ob', null);
    },

    reset: function() {
        this.is_top = this.is_bottom = this.is_end_of_data = false;

        if (!is_null(this.container)) {
            var size = this.container.find(".subline").length || 0;
            this.per_page = size;
        } else
            this.per_page = 0;

        if (this.number > this.per_page)
            this.number = this.per_page;
    },

    get_id: function() {
        return $_get_item_id(this.current, -1);
    },

    get_current: function() {
        return this.current;
    },

    set_current: function(ob) {
        if (is_null(ob))
            return;

        this.current = ob;
        this.oid = ob.attr('id');
        this.number = parseInt($_get_item_id(ob, -1));

        if (this.IsLog)
            console.log('$SublineSelector.set_current:'+is_null(this.current)+':'+this.oid+':'+this.number);

        $ActiveSelector.reset(this);
    },

    onRefresh: function(ob) {
        if (ob === null) {
            SelectedSetItem(this.alias, 'ob', null);
            this.is_end_of_data = true;

            $ActivateInfoData(0);
        }

        this.set_current(ob);
        return this._refresh(0);
    },

    onProgress: function(ob) {
        return isWebServiceExecute;
    },

    _find: function(num) {
        var ob = null;

        if (is_null(num) || num <= 0)
            return null;

        this.container.find(".subline").each(function(index, x) {
            if (this.IsTrace)
                alert('$SublineSelector._find'+$(x).attr('id')+':'+parseInt($_get_item_id($(x), -1)));
            if (parseInt($_get_item_number($(x), -1)) == num)
                ob = $(x);
        });

        if (this.IsTrace)
            alert('$SublineSelector._find'+'found:'+(ob ? ob.attr('id') : 'null'));

        return ob;
    },

    _refresh: function(new_page) {
        var exit = true;
        var line;

        if (this.IsLog)
            console.log('$SublineSelector._refresh:'+new_page+':'+this.is_top+':'+this.is_bottom+':'+this.is_end_of_data);

        // --------------------
        // Refresh current page
        // --------------------

        if (new_page == 0 && !(this.is_top || this.is_bottom || this.is_end_of_data)) {
            $HideLogPage();

            SelectedSetItem(this.alias, 'ob', this.current);
            //$onToggleSelectedClass(SUBLINE, this.current, 'submit', null);

            $ShowSubline();
        } 
        else
            exit = false;

        return exit;
    },

    _move: function(direction, number) {
        var is_found = false;
        var num = 0;

        // ------------------------
        // Move inside current page
        // ------------------------

        if ((direction > 0 && this.number < this.per_page) || (direction < 0 && this.number > 1))
            num = this.number + (direction > 0 ? 1 : -1);
        else if (direction == 0 && !is_null(number))
            num = number;
        
        var ob = this._find(num);

        if (!is_null(ob)) {
            this.set_current(ob);
            is_found = true;
        }

        this.reset();

        if (!is_found) {
            this.is_end_of_data = (
                (direction < 0 && this.page == 1) || 
                (direction > 0 && this.page == this.pages)
                ) ? true : false;

            this.is_top = (direction < 0 && !this.is_end_of_data) ? true : false;
            this.is_bottom = (direction > 0 && !this.is_end_of_data) ? true : false;
        }

        if (this.IsTrace)
            alert('$SublineSelector._move'+'move:'+this.number+':'+this.is_top+':'+this.is_bottom+':'+this.is_end_of_data);

        return is_found || this.is_top || this.is_bottom;
    },

    is_movable: function() {
        return !this.is_end_of_data && this.per_page > 0 ? true : false;
    },

    home: function() {
        return this._move(0, 1) === true ? this._refresh(0) : false;
    },

    up: function() {
        return this._move(-1) === true ? this._refresh(0) : false;
    },

    down: function() {
        return this._move(1) === true ? this._refresh(0) : false;
    },

    end: function() {
        return this._move(0, this.per_page) === true ? this._refresh(0) : false;
    }
};

var $TabSelector = {
    container : null,

    // ===================
    // Tabs Selector Class
    // ===================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    current   : null,
    number    : 0,
    count     : 0,

    init: function() {
        this.container = $("#tab-content");

        if (is_exist(this.container)) {
            this.count = this.container.children().length;
        }

        if (this.IsTrace)
            alert('$TabSelector.count:'+this.count);

        this.reset();
    },

    reset: function() {
        this.set_current(1);
    },

    set_current: function(num) {
        this.number = num;
    },

    get_current: function() {
        return this.current;
    },

    set_current_by_id: function(id) {
        var ob = $("#"+id, this.container);

        if (this.IsLog)
            console.log('$TabSelector.set_current_by_id:'+id, ob);

        this.onClick(ob);
    },

    onClick: function(ob) {
        var id = ob.attr('id');
        this.onMove(id);

        if (id != default_menu_item)
            $SublineSelector.release();

        if (typeof $onTabSelect === 'function')
            $onTabSelect(ob);
    },

    onMove: function(id) {
        this._move(id);
    },

    _move: function(id) {
        if (this.count == 0)
            return;

        var is_found = false;
        var number = 1;

        var menu = this.container.find(".menu");

        if (is_exist(menu)) {
            menu.each(function(index, x) {
                if ($(x).attr('id') == id)
                    is_found = true;
                if (!is_found)
                    ++number;
            });

            this.number = number;
        }

        if (this.IsLog)
            console.log('$TabSelector._move:'+id+':'+this.number);
    },

    _find: function(direction) {
        if (this.count == 0) 
            return;

        var num = this.number + direction;
        var number = num > this.count ? 1 : (num == 0 ? this.count : num);
        var found_ob = null;
        var last_ob = null;

        this.container.find(".menu").each(function(index, x) {
            var ob = $(x);
            var i = index + 1;
            var is_invisible = ob.hasClass(CSS_INVISIBLE);

            if ($TabSelector.IsTrace)
                alert('$TabSelector._find'+ob.attr('id')+':'+index+':'+number);
            if (found_ob == null) {
                if (i > number && direction == 1) {
                    if (!is_invisible)
                        found_ob = ob;
                }
                else if (i == number) {
                    if (!is_invisible)
                        found_ob = ob;
                    else if (direction == -1 && last_ob != null)
                        found_ob = last_ob;
                }
                else {
                    if (!is_invisible)
                        last_ob = ob;
                }
            }
        });

        this.number = number;

        if (this.IsTrace)
            alert('$TabSelector._found'+'found:'+(found_ob ? found_ob.attr('id') : 'null'));

        return found_ob;
    },

    _refresh: function(direction) {
        var ob = this._find(direction);
        if (!is_null(ob)) {
            if (typeof $onTabSelect === 'function')
                return $onTabSelect(ob);
        }
        return false;
    },

    left: function() {
        return this._refresh(-1);
    },

    right: function() {
        return this._refresh(1);
    },

    tab: function() {
        return this.right();
    }
};

// ==================
// Main Menu Selector
// ==================

function controller_menu_item(ob) {
    return $("a", ob);
}

var $MenuSelector = {
    container : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    current   : null,
    number    : 0,
    count     : 0,
    items     : null,
    id        : null,

    init: function(id) {
        this.container = $("#mainmenu ul");
        this.items = $("li", this.container);
        this.count = this.items.length;

        if (this.IsTrace)
            alert('$MenuSelector.init:'+'.count:'+this.count);

        this.set_current('mainmenu-'+id);
    },

    set_current: function(id) {
        var current = null;
        var num = 0;
        this.items.each(function() {
            var ob = controller_menu_item($(this));
            if (is_null(current)) {
                if (ob.prop("id") == id)
                    current = ob;
                ++num;
            }
        });
        this.current = current;
        this.number = num;
        this.id = id;

        if (this.IsDebug)
            alert('$MenuSelector.set_current:'+this.id+':'+this.number);
    },

    get_current: function() {
        return this.current;
    },

    set_current_by_id: function(id) {
        var ob = $("#"+id, this.container);

        if (this.IsLog)
            console.log('$MenuSelector.set_current_by_id:'+id, ob);

        this.onClick(ob);
    },

    onClick: function(ob) {
        var id = ob.attr('id');

        this.onMove(id);

        if (typeof $onMenuSelect === 'function')
            $onMenuSelect(ob);
    },

    onMove: function(id) {
        this._move(id);
    },

    _move: function(id) {
        var is_found = false;
        var number = 1;

        this.items.each(function(index, x) {
            if ($(x).attr('id') == id)
                is_found = true;
            if (!is_found)
                ++number;
        });

        this.number = number;

        if (this.IsLog)
            console.log('$MenuSelector._move:'+id+':'+this.number);
    },

    _find: function(direction) {
        var num = this.number + direction;
        var number = num > this.count ? 1 : (num == 0 ? this.count : num);
        var found_ob = null;
        var last_ob = null;

        this.items.each(function(index, x) {
            var ob = $(x);
            var i = index + 1;
            var is_invisible = ob.hasClass(CSS_INVISIBLE);

            if ($MenuSelector.IsDebug)
                alert('$MenuSelector._find:'+ob.attr('id')+':'+index+':'+number);

            if (found_ob == null) {
                if (i > number && direction == 1) {
                    if (!is_invisible)
                        found_ob = ob;
                }
                else if (i == number) {
                    if (!is_invisible)
                        found_ob = ob;
                    else if (direction == -1 && last_ob != null)
                        found_ob = last_ob;
                }
                else {
                    if (!is_invisible)
                        last_ob = ob;
                }
            }
        });

        this.number = number;

        if (this.IsTrace)
            alert('$MenuSelector.found:'+this.number);

        return found_ob;
    },

    _refresh: function(direction) {
        var ob = this._find(direction);
        if (!is_null(ob)) {
            if (typeof $onMenuSelect === 'function')
                return $onMenuSelect(controller_menu_item(ob));
        }
        return false;
    },

    left: function() {
        return this._refresh(-1);
    },

    right: function() {
        return this._refresh(1);
    },
};

var $DblClickAction = {
    control   : null,

    // =========================
    // DoubleClick Handler Class
    // =========================

    clicks    : 0,
    timeout   : 300,
    timer     : null,

    single    : null,
    double    : null,

    reset: function() {
        this.control = null;
        this.clicks = 0;
        this.timer = null;
        this.single = null;
        this.double = null;
    },

    click: function(single, double, control, timeout) {
        this.control = control;
        this.single = single;
        this.double = double;

        this.clicks++;

        if (this.clicks === 1) {

            this.timer = setTimeout(function() {
                var self = $DblClickAction;

                // -------------------
                // Single-click action
                // -------------------

                self.single && self.single(self.control);
                self.reset();

            }, timeout || this.timeout);

        } else if (!is_null(this.timer)) {

            // -------------------
            // Double-click action
            // -------------------

            clearTimeout(this.timer);

            this.single && this.single(this.control);
            this.double && this.double(this.control);
            this.reset();

        }
    }
};

var $DraggableImage = {
    image     : null,
    params    : new Object(),

    // =======================
    // Draggable Image Handler
    // =======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    set_param: function(params, key, value) {
        this.params[key] = getObjectValueByKey(params, key) || value;
    },

    get_param: function(key) {
        return this.params[key];
    },

    init: function(params) {
        this.set_param(params, 'width_padding', 0);
        this.set_param(params, 'height_padding', 0);

        if (this.IsLog)
            console.log('init', this.params);

        this.image = null;
    },

    onEnter: function(ob, id, e) {
        if (is_null(ob))
            ob = $(e.target);

        if (is_null(this.image)) {
            var control = $("#"+id);

            if (is_null(control))
                return;

            this.image = {
                'ob'        : ob, 
                'id'        : id,
                'control'   : control, 
                'width'     : control.width() + this.get_param('width_padding'), 
                'height'    : control.height() + this.get_param('height_padding')
            }; 

            this.image.ob.css({ 'cursor':'pointer' });
            this.image.control.removeClass('hidden');
        }

        if (this.IsDebug)
            console.log('enter', (!is_null(this.image) ? this.image.id : null), e.pageX, e.pageY);

        if (this.IsDebug)
            console.log('screen', $_height('screen-max'), $_width('screen-max'));
    },

    onLeave: function(e) {
        if (this.IsLog)
            console.log('leave', e.pageX, e.pageY);

        if (!is_null(this.image)) {
            this.image.control.addClass('hidden');
            this.image.ob.css({ 'cursor':'default' });

            this.image = null;
        }
    },

    onMove: function(e) {
        if (is_null(this.image)) 
            return;

        var scrolltop = int($(window).scrollTop());
        var x = e.pageX;
        var y = e.pageY;
        var top = 0;
        var left = 0;
        var height_limit = int($_height('screen-max') / 2.5);
        //var ob_left = this.image.ob.position().left;
        //var size_width = int(($_width('max') - this.image.width) / 2);

        if (y - scrolltop > height_limit) {
            top = y - this.image.height - 10;
            left = x - this.image.width - 10;
        }
        else {
            top = y + 20;
            left = x - this.image.width - 10;
        }

        var screen_width = $_width('screen-max');

        if (x - this.image.width < 0 || x + this.image.width > screen_width - 20)
            //left = x - int((screen_width - this.image.width) / 2);
            left = x - int(this.image.width / 2);

        //console.log(left + this.image.width, screen_width);

        if (left + this.image.width > screen_width - 20)
            left = screen_width - this.image.width - 20;

        if (this.IsLog)
            console.log('move', x, y, top, left, scrolltop, this.image.control.attr('id'));

        this.image.control.offset({ top: top, left: left });
    }
};

// ===============
// Action handlers
// ===============

function $GetLog(action, callback) {
}

function $GetLogItem(source) {
}

// =====================
// Page Scroller Handler
// =====================

var $TablineSelector = {
    container : null,

    // ======================
    // Tabline Selector Class
    // ======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ----------------
    // Config Object ID
    // ----------------

    alias     : '',         // Tabline Object name
    mode      : '',         // The same as `group` XXX !!!
    
    // ------------------------------------------------
    // Current page: page=pages=1, per_page:rows number
    // ------------------------------------------------

    current   : null,
    oid       : '',
    number    : 0,

    page      : 0,
    pages     : 0,
    per_page  : 0,
    lines     : 0,
    line      : 0,

    with_chunk: 1000,
    chunk     : null,
    next_chunk: null,
    next_row  : null,

    is_top    : false,
    is_bottom : false,

    is_end_of_data : false,

    init: function(tab, group, per_page, total_rows) {
        if (!is_empty(group)) {
            this.alias = 'tabline-'+group;
            this.mode = group;
        } else if (is_exist(tab)) {
            this.alias = TABLINE;
            this.set_mode(tab);
        }

        this.set_total_rows(total_rows);

        this.container = $("#"+this.get_mode()+"-container");

        if (this.IsLog)
            console.log('$TablineSelector.init, mode:'+this.get_mode(), 'alias:'+this.alias, this.container);

        this.release();

        var ob = null;

        if (is_exist(this.container)) {
            ob = this._get_selected();
        } else {
            this.container = null;
            return;
        }

        this.page = 1;
        this.pages = 1;
        this.per_page = is_empty(per_page) ? Math.min(10, this.lines) : per_page;
        this.line = 1;

        if (!is_null(ob))
            SelectedSetItem(this.mode, 'ob', ob);

        this.reset();

        this.onRefresh(ob);
    },

    set_total_rows: function(value) {
        if (value)
            this.lines = value;
    },

    _get_selected: function() {
        var obs = $("tr[class~='tabline']", this.container);
        var ob = $("tr[class~='selected']", this.container).first();
        if (is_null(ob) || is_empty(ob.attr('id'))) {
            //ob = this.container.find("tr[class~='tabline']").first();
            ob = obs.first();

            if (this.IsLog)
                console.log('$TablineSelector_get_selected:no data:', ob, this.lines, obs.length);

            if (ob.length == 0) {
                this.current = null;
                ob = null;
            }
        }

        if (this.lines == 0) {
            this.lines = obs.length;
        }
        this.chunk = [0, Math.min(this.with_chunk, this.lines)];

        return ob;
    },

    release: function() {
        this.current = null;
        this.oid = '';
        this.number = 0;

        SelectedSetItem(this.mode, 'ob', null);
    },

    reset: function() {
        this.is_top = this.is_bottom = this.is_end_of_data = false;

        //var size = this.container.find(".tabline").length || 0;
        // XXX monopage (no paging)
        if (is_empty(this.per_page) || this.per_page < 0)
            this.per_page = this.lines;

        if (this.per_page && this.number > this.per_page && this.pages > 1)
            this.number = this.per_page;

        if(this.IsDebug)
            alert(joinToPrint(['$TablineSelector.reset.alias:', this.alias, 
                this.per_page, this.lines, this.pages, this.number]));
    },

    get_mode: function() {
        return this.mode;
    },

    set_mode: function(ob) {
        this.mode = !is_null(ob) ? ob.attr('id').split('-').slice(-1)[0] : null;
    },

    set_per_page: function(value) {
        this.per_page = value;
    },

    get_id: function() {
        return !is_null(this.current) ? $_get_item_id(this.current, -1) : null;
    },

    get_current: function() {
        return this.current;
    },

    set_current: function(ob) {
        if (is_null(ob))
            return;

        this.current = ob;
        this.oid = ob.attr('id');
        this.number = parseInt($_get_item_number(ob, -1));

        SelectedSetItem(this.mode, 'ob', ob);

        if (this.IsLog)
            console.log('$TablineSelector.set_current:', this.alias, this.oid, ob, this.number);

        $ActiveSelector.reset(this);
    },

    set_current_by_id: function(id) {
        var ob = null;
        if (!is_null(this.container)) {
            ob = $("tr[id^='row-"+this.alias+"_"+id+"']", this.container);    
        }
        if (!is_exist(ob))
            ob = this._get_selected();

        if (this.IsLog)
            console.log('$TablineSelector.set_current_by_id:', id, ob);

        this.onRefresh(ob);
    },

    onRefresh: function(ob) {
        if (is_null(ob)) {
            SelectedSetItem(this.mode, 'ob', null);
            ob = this.get_current();
        }

        this._remove();
        this.set_current(ob);
        return this._refresh(0);
    },

    onProgress: function(ob) {
        return false;
    },

    _remove: function() {
        var ob = this.current;
        if (!is_null(ob)) {
            $onToggleSelectedClass(this.mode, ob, 'remove', null);
        }

        if (this.IsLog)
            console.log('$TablineSelector._remove:', this.mode, this.oid, ob, this.number);
    },

    _refresh: function(new_page) {
        var exit = true;
        var line;

        // --------------------
        // Refresh current page
        // --------------------

        var ob = this.current;

        if (this.IsLog)
            console.log('$TablineSelector._refresh:', this.alias, this.oid, ob, this.number);

        if (new_page == 0 && is_exist(ob)) { 
            $onToggleSelectedClass(this.mode, ob, 'add', null);
        } 
        else
            exit = false;

        if (typeof $onTablineSelect === 'function')
            $onTablineSelect(ob, this.mode);

        return exit;
    },

    get_next_chunk: function() {
        return {'chunk': this.chunk, 'next_chunk':this.next_chunk, 'with_chunk': this.with_chunk, 
            'next_row': this.next_row, 'number':this.number, 'id':this.get_id()};
    },

    get_chunk: function() {
        return this.chunk;
    },

    set_chunk: function(chunk, num, direction) {
        if (this.IsLog)
            console.log('$TablineSelector.set_chunk:', chunk, num, direction);

        this.chunk = chunk;
        this.next_chunk = null;
        this.next_row = null;

        this.locate(num - this.chunk[0] + 1, direction);
    },

    get_number: function(num, is_check_chunk) {
        var number = (num > 0 ? num : this.number);

        if (is_check_chunk) {
            if (!this._is_inside_chunk)
                this.number = number;
        }

        if (this.IsLog)
            console.log('$TablineSelector.get_number:', this.chunk, num, this.number, number);

        return number;
    },

    _is_inside_chunk: function(num) {
        if (!is_null(this.chunk)) {
            if (num > this.chunk[0] && num <= this.chunk[1])
                return 1;
        }
        return 0;
    },

    _is_outer_chunk: function(num) {
        var inside = 0, outside = 0;
        var top = 0, bottom = 0;
        var is_exit = false;
        if (this.lines > this.with_chunk) {
            if (this.number > this.chunk[0] && this.number <= this.chunk[1])
                inside = 1;
            if (this.number > this.chunk[1] && this.lines > this.chunk[1])
                outside = 1;
            if (num > this.chunk[1]) {
                bottom = Math.min(this.chunk[1]+this.with_chunk, this.lines);
                top = this.chunk[1]+1;
                this.next_chunk = [top, bottom];
                is_exit = true;
            }
            else if (num < this.chunk[0]) {
                bottom = Math.max(this.with_chunk, this.chunk[1]-this.with_chunk);
                top = bottom - this.with_chunk + 1;
                this.next_chunk = [top, bottom];
                is_exit = true;
            }
        }

        if (this.IsLog)
            console.log('$TablineSelector._is_outer_chunk:', num,  inside, outside, this.chunk, 
                top, bottom, this.next_chunk,  is_exit);

        return is_exit;
    },

    _move: function(direction, number) {
        var num = 0;

        // ------------------------
        // Move inside current page
        // ------------------------

        if ((direction > 0 && this.number < this.lines) || (direction < 0 && this.number > 1))
            num = this.number + direction*(number ? number : 1);
        else if (direction == 0 && !is_empty(number))
            num = Math.min(Math.max(number, 1), this.lines);
        
        if (this._is_outer_chunk(num)) {
            this.next_row = num;
            if (typeof $onTablineUpload === 'function') {
                if ($onTablineUpload(this.alias))
                    return;
            }
        }
        this.locate(num, direction);
    },

    _find: function(num) {
        var self = this;
        var ob = null;

        if (!is_empty(num)) {
            var number = self.get_number(num, 1);
            if (number > 0) {
                this.container.find(".tabline").each(function() {
                    if (self.IsDebug)
                        alert('$TablineSelector._find:'+$(this).attr('id')+':'+parseInt($_get_item_id($(this), -1)));

                    if (parseInt($_get_item_number($(this), -1)) == number)
                        ob = $(this);
                });
            }
        }

        if (this.IsLog)
            console.log('$TablineSelector._find:', num,  ob);

        return ob;
    },

    locate: function(num, direction) {
        var is_found = false;
        var ob = this._find(num);

        if (is_exist(ob)) {
            this._remove();
            this.set_current(ob);
            this.number = parseInt($_get_item_number(ob, -1));
            is_found = true;
        }

        this.reset();

        if (!is_found) {
            this.is_end_of_data = this.number == this.lines;
            this.is_top = (direction < 0 && !this.is_end_of_data);
            this.is_bottom = (direction > 0 && !this.is_end_of_data);
        }

        if (this.IsLog)
            console.log('$TablineSelector._move:', this.number, num, this.per_page,
                this.is_top, this.is_bottom, this.is_end_of_data);

        return is_found;
    },

    is_movable: function() {
        return !this.is_end_of_data && this.per_page > 0 ? true : false;
    },

    home: function() {
        if (this.IsDebug)
            alert('home:'+this.pages+':'+this.lines+':'+this.per_page);
        return this._move(0, 1) ? this._refresh(0) : false;
    },

    up: function() {
        if (this.IsDebug)
            alert('up:'+this.pages+':'+this.lines+':'+this.per_page);
        return this._move(-1) ? this._refresh(0) : false;
    },

    down: function() {
        if (this.IsDebug)
            alert('down:'+this.pages+':'+this.lines+':'+this.per_page);
        return this._move(1) ? this._refresh(0) : false;
    },

    pgup: function() {
        if (this.IsDebug)
            alert('pgup:'+this.pages+':'+this.lines+':'+this.per_page);
        return this._move(0, this.number-this.per_page) ? this._refresh(0) : false;
    },

    pgdown: function() {
        if (this.IsDebug)
            alert('pgdown:'+this.pages+':'+this.lines+':'+this.per_page);
        //return this._move(1) === true ? this._refresh(0) : false;
        return this._move(0, this.number+this.per_page) === true ? this._refresh(0) : false;
    },

    end: function() {
        if (this.IsDebug)
            alert('end:'+this.pages+':'+this.lines+':'+this.per_page);
        return this._move(0, this.pages == 1 ? this.lines: this.per_page) === true ? this._refresh(0) : false;
    }
};

function tab_init(group, per_page) {
    var total_rows = parseInt($("#"+group+'-rows-total').html());
    $TablineSelector.init(null, group, per_page, total_rows);
    tablines[group] = Object.assign({}, $TablineSelector);
    if (controllers.indexOf(group) == -1){
        controllers.push(group);
        tabs = Object.keys(tablines).length;
    }

    $PageScroller.init(group, true);

    if (IsLog)
        console.log('db.controller.tab_init:', group, tablines, tabs);
}

function init_selector(column, row) {
    /*****
     *  Tab Selector:
     *      container -- html-container of tab
     *      base      -- group base-container
     *      group     -- name of reference, ie:[nodes]
     *      mode      -- DB model (form id="{{ mode }}-form"), ie:[node]
     *      column    -- selected column (control)
     *      row       -- selected row (control)
     *      tab       -- Tab container (class="view-container" id="tabline-{{ group }}", control)
     *      id        -- id of selected row
     *      row_id    -- id of last updated row by default_log_action
     *      active    -- flag, any tabline is active (selected)
     *
     ****/

    var tab = null;

    if (!is_null(column)) {
        tab = column.closest(".view-container");
        row = column.closest(".tabline");
    } else if (!is_null(row)) {
        tab = row.closest(".view-container");
    } else {
        selector = {
            'group' : group, 
            'mode' : mode, 
        };
        return false;
    }

    var group = is_exist(tab) ? tab.attr('id').split('-')[1] : null;
    var container = $("#tabline-"+group);
    var base = $("#"+group);

    if (IsLog)
        console.log('db.controller.init_selector:tab', tab, row, is_exist(tab), is_exist(row), group, base);

    var mode = group.slice(0,-1);

    if (IsDebug)
        alert('tabline:group'+group+', mode:'+mode+', row_id:'+row.attr('id'));

    selector = {
        'container':container,
        'base' : base,
        'group' : group, 
        'mode' : mode, 
        'column' : column, 
        'row' : row, 
        'tab' : tab, 
        'id' : row.attr('id'),
        'row_id' : '',
        'active' : 0,
    };

    if (IsLog)
        console.log('db.controller.init_selector:selector', selector);

    var group = selector.group;
    var mode = selector.mode;
    var column = selector.column;
    var row = selector.row;
    var id = row.attr('id');

    if (IsDebug)
        alert(joinToPrint([group, id, row.attr('id'), mode]));

    tablines[group].onRefresh(row);

    return true;
}

function init_controller(group) {
    if (is_null(group)) {
        var index = active_controller >= tabs-1 ? 0 : active_controller+1;
        group = controllers[index];
    }

    if (is_null(group))
        return;

    //alert('init_controller.before.group:'+group);
    if ($PageScroller.init_state(tablines[group].get_current(), true))
        $PageScroller.activate_group();
    //alert('init_controller.after.group:'+group+':'+tabs+':'+active_controller);
}

function get_chunk_begin(chunk) {
    return (!is_empty(chunk) && chunk.length > 0) ? chunk[0]-1 : 0;
}

var $PageScroller = {
    groups    : new Object(),
    container : null,
    control   : null,
    base      : null,
    template  : { 
        'container' : null, 'box':null, 'base': null,
        'default_position':0, 'position'  : 0, 'top':0, 'height':0, 'per_page':0, 'isDefault':0, 'init_is_done':0 },
    position  : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    row_is_top_in_container : 1,

    init: function(group, force) {
        if (this.IsTrace)
            console.log('$PageScroller.init:group:', group);

        if (is_empty(group))
            return;

        if (force && (group in this.groups))
            this.groups[group].init_is_done = false;

        var ob = getattr(this.groups, group, null);
        this.container = getattr(ob, 'container');

        if (is_null(ob) || !is_exist(this.container)) {

            if (this.IsDebug)
                alert('$PageScroller.init.group:'+group+':'+joinToPrint(objectKeys(this.groups)));

            this.container = $("#tabline-"+group);
            this.box = $("#"+group+"-container", this.container);
            this.groups[group] = Object.assign({}, this.template);
            this.groups[group].container = this.container;
            this.groups[group].base = $("#"+group);
            this.control = this.groups[group];
            this.control.container = this.container;
            this.control.box = this.box;
        }
        
        this.control.position = this.container.scrollTop();

        this.control.default_position = this.control.top = this.container.position().top;

        if (this.IsLog)
            console.log('$PageScroller.init:group', group, this.control, this.groups);

        this.init_position(group);
    },

    activate: function(group, row_id, next_row, chunk) {
        if (this.IsLog)
            console.log('$PageScroller.activate.before:', group, row_id, this.container);

        tab_init(group);

        var tabline = tablines[group];
        if (!is_empty(chunk))
            tabline.set_chunk(chunk, next_row, 0);
        else
            tabline.set_current_by_id(row_id);
        
        var row = tabline.get_current();

        if (this.IsLog)
            console.log('$PageScroller.activate.after:', group, row_id, next_row, row);

        if (!is_exist(row))
            return;

        this.refresh(group, 'reset');
    },

    get_container_position: function(group) {
        this.container = this.groups[group].container;
        if (is_null(this.container))
            return;

        var head = $("#"+group+"-header", this.container);
        var header = is_exist(head) ? head.outerHeight() : 0;
        var top = this.container.position().top;
        var height = this.container.height();
        return { 'top':top, 'height':height, 'header': header, 'id':this.container.attr('id') };
    },

    init_position: function(group) {
        if (this.IsTrace)
            console.log('$PageScroller.init_position.group:', group, this.groups[group]);

        if (this.groups[group].init_is_done)
            return;

        var container_position = this.get_container_position(group);
        var top = container_position.top;
        var height = container_position.height;
        var header = container_position.header;
        var obs = $("tr[class~='tabline']", this.container);
        var per_page = 0;
        
        if (is_empty(obs))
            return;

        obs.each(function(index){
            var row = $(this);
            var row_top = row.position().top;
            var row_height = row.height();
            if (row_top > top+header && row_top+row_height < top+height)
                per_page += 1;
        });

        this.groups[group].per_page = per_page;
        this.groups[group].init_is_done = true;

        //alert('$PageScroller.init_position:'+group+':'+per_page);

        if (this.IsTrace)
            console.log('$PageScroller.init_position.per_page:', group, per_page);

        tablines[group].set_per_page(per_page);
    },

    reset: function(force, timeout) {
        if (force)
            this.resize();
        else
            sleep(function() { this.resize(); }, timeout || 500);
    },

    resize: function() {
        clear_timeout();
        resize();
    },

    trace: function(force) {
    
    },

    init_state: function(ob, force) {
        if (this.IsTrace)
            console.log('$PageScroller.init_state:', ob);

        this.deactivate_group();

        if (!init_selector(null, ob))
            return false;

        var group = selector.group;

        this.init(group, force);

        if (typeof $onTabSelect === 'function')
            $onTabSelect(group);

        this.checkPosition(group);

        return true;
    },

    refresh: function(group, command) {
        if (is_empty(group))
            group = selector.group;

        var force = false;

        if (this.IsTrace)
            console.log('$PageScroller.refresh.group:', group, command);

        var tabline = tablines[group];

        switch (command) {
        case 'first':
            tabline.home();
            break;
        case 'up':
            if (!tabline.is_top && tabline.number > 1)
                tabline.up();
            break;
        case 'down':
            if (!tabline.is_bottom && tabline.number < tabline.lines)
                tabline.down();
            break;
        case 'pgup':
            if (!tabline.is_top && tabline.number > 1)
                tabline.pgup();
            break;
        case 'pgdown':
            if (!tabline.is_bottom && tabline.number < tabline.lines)
                tabline.pgdown();
            break;
        case 'last':
            tabline.end();
            break;
        default:
            tabline.onRefresh(null);
            force = true;
        }

        this.init_state(tabline.get_current(), force);
    },

    activate_group: function() {
        if (selector.active) {
            for (var key in this.groups) {
                var box = getattr(this.groups[key], 'base');
                if (is_exist(box))
                    box.removeClass('active');
            }
        }

        if (this.IsLog)
            console.log('$PageScroller.activate_group', controllers, selector);

        selector.base.addClass('active');
        active_controller = controllers.indexOf(selector.group);
        selector.active = 1;
    },

    deactivate_group: function() {
        if (!is_null(selector)) {
            if (is_exist(getattr(selector, 'base'))) {
                selector.base.removeClass('active');
            }
            selector.active = 0;
        }
    },

    checkPosition: function(group) {
        if (!group || is_null(this.groups))
            return;

        if (is_null(getattr(this.groups, group, null)))
            this.init(group);

        this.activate_group();

        var container_position = this.get_container_position(group);

        this.position = this.container.scrollTop();
        this.control = this.groups[group];

        if (this.IsTrace)
            console.log('$PageScroller.checkPosition.group:', group, this.position, this.container, this.control);

        this.tabline = tablines[group];

        var box = this.control.box;
        var box_height = box.height();
        var top = container_position.top;
        var height = container_position.height;
        var header = container_position.header;
        var id = this.tabline.get_id();
        var row = this.tabline.get_current();
        var row_id = row.attr('id');
        var row_top = row.position().top;
        var row_height = row.height();
        var row_position = { 'row_top':row_top, 'row_height':row_height, 'row_id':row_id, 'id':id };

        if (this.IsLog)
            console.log('$PageScroller.checkPosition.group.position:', group, box_height, container_position, row_position);

        this.control.position = this.container.scrollTop();

        var number = this.tabline.number;
        var scroll = this.control.position;

        var p = 'inside';
        var tc = top+header;
        var bc = top+height;
        var tr = row_top;
        var br = row_top+row_height;
        var x = br-bc;
        if (tr < tc) {
            p = 'up';
            scroll += tr-tc;
        }
        else if (br > bc) {
            p = 'down';
            if (this.row_is_top_in_container)
                scroll += tr-tc;
            else
                scroll += x;
        }
        else if ((row_top-top) < 0 || this.tabline.is_top) {
            p = 'top';
            scroll = 0;
        }
        else if ((br-top == box_height) || this.tabline.is_bottom) {
            p = 'end';
            scroll = box_height-row_height;
        }

        if (this.IsDebug)
            alert(p+':'+scroll);

        if (this.IsLog)
            console.log('$PageScroller.checkPosition.scroll:', scroll, number, p, tr, tc, br, bc, top, header, height);
        
        var selected = $("#"+group+"_row_selected"); //, this.groups[group].base
        if (is_exist(selected)) {
            selected.html(number);
        }

        if (this.IsLog)
            console.log('$PageScroller.checkPosition.selected:', group, number, selected);

        this.container.scrollTop(Math.ceil(scroll));
        this.control.position = this.container.scrollTop();
    },

    move: function() {}
};

// ============
// WEB-SERVICES
// ============

function $web_free() {
/***
 *  Semaphore: is controller busy or not true|false.
 */
    return !isWebServiceExecute ? true : false;
}

function $is_shown_error() {
/***
 *  Semaphore: is error shown on the screen true|false.
 */
    return is_show_error ? true : false;
}

function $web_busy() {
/***
 *  Semaphore: is controller busy true|false.
 */
    return (isWebServiceExecute || is_show_error) ? true : false;
}

function $web_uploader(action, data, handler) {
/***
 *  Storage Data Uploader AJAX-backside handler.
 *  Used to download/upload files.
 *
 *  Action:        action number (000-999)
 *  Data:          data of file to upload
 *  Handler:       handler (to process the returned data)
 *
 *  Hard link.
 */
    if (!$web_free())
        return;

    if (IsLog)
        console.log('$web_uploader:', action);

    // ------------
    // START ACTION
    // ------------

    is_loaded_success = false;

    $ShowSystemMessages(true, true);
    $ShowLoader(1);

    $.ajax({
        type: 'POST',
        url: $SCRIPT_ROOT + '/storage/uploader',
        data: data,
        contentType: false,
        cache: false,
        processData: false,
        //async: false,

        success: function(x, status, ob) {
            is_loaded_success = true;

            $ShowLoader(-1);

            var errors = x['errors'];

            if (!is_empty(errors)) {
                var msg = errors.join('<br>');
                $ShowError(msg, true, true, false);
            }

            else if (!is_null(handler)) {

                var t = typeof handler;

                if (IsTrace)
                    alert('$web_uploader.handler:'+action+':'+t);

                handler(x);
            }
        },
        
        error: function(ob, status, error) {
            is_loaded_success = false;

            $ShowLoader(-1);
        },

        complete: function(ob, status) {
            if (IsLog)
                console.log('$web_uploader.complete, status:', status, is_loaded_success);
        }
    });
}

function $web_logging(action, handler, params) {
/***
 *  General AJAX-backside handler.
 *  Used to interact with the core of the application.
 *
 *  Action:        action number (000-999)
 *  [Handler]:     handler (to process the returned data)
 *  [Params]:      query data (object)
 *
 *  System args and state-items:
 * 
 *  $SCRIPT_ROOT - root-part of URL
 *  loader_page  - page name, may be omitted (provision|workflow...)
 *  loaderURI    - path to backside handler (/loader)
 * 
 *  isWebServiceExecute: loader is busy 1|0
 *  is_show_error: got error or not 1|0
 * 
 *  Hard link.
 */
    var uri = $SCRIPT_ROOT + loader_page + loaderURI;

    if (IsDeepDebug)
        alert('>>> web_logging.uri:'+uri+', action:'+action+':'+isWebServiceExecute+':'+is_show_error);

    if ($web_busy())
        return;

    var current_action = action;
    var args = new Object();

    if (IsLog) {
        console.log('$web_logging, action:', action, selected_menu_action, uri);
    }

    // -----------------------
    // Check Action parameters
    // -----------------------

    $PageController.init(action, default_action);

    args = {
        'action' : action,
        'selected_menu_action' : selected_menu_action,
    };

    if (action == default_action) {

        current_action = $PageController.default_action(action, args);

        if (IsLog) {
            console.log('web_logging.defailt_action.args:', action, args);
        }
    } else {

        $PageController.action(action, args, params);

    }

    if (IsLog) {
        console.log('web_logging.action.args:', args);
    }

    if (!is_null(params))
        args['params'] = jsonify(params);

    args['current_sort'] = current_sort;

    var error = {
        'exchange_error'    : 0, 
        'exchange_message'  : '', 
        'error_description' : '', 
        'error_code'        : '', 
        'errors'            : ''
    };

    if (IsLog) {
        console.log('$web_logging, args with params:', args, current_action);
    }

    // ------------
    // START ACTION
    // ------------

    $TriggerActions(true);

    is_loaded_success = false;

    if (IsLog) {
        console.log('$web_logging.uri:', $SCRIPT_ROOT+loaderURI);
    }

    $ShowSystemMessages(true, true);
    $ShowLoader(1);

    $.post(uri, args, function(response) {
        var action = response['action'];

        // -----------------------
        // Server Exchange erorors
        // -----------------------

        error.exchange_error = parseInt(response['exchange_error'] || 0);
        error.exchange_message = response['exchange_message'];

        if (IsTrace)
            alert('$web_logging.post:'+action);

        if (IsLog)
            console.log('$web_logging.post:'+action+':'+current_action+':'+default_action, 'error:', error.exchange_error);

        var total = parseInt(response['total'] || 0);
        var status = response['status'];
        var path = response['path'];
        var data = response['data'];
        var props = response['props'];
        var columns = response['columns'];

        var refresh_state = true;

        // --------
        // RESPONSE
        // --------

        $ShowLoader(-1);

        if (typeof log_callback_error === 'function' && should_be_updated) {
            var errors = response['errors'];
            log_callback_error(action, errors);
        }

        if (error.exchange_error)
            refresh_state = false;

        else if (!is_null(handler)) {

            var type_of_handler = typeof handler;

            if (IsTrace)
                alert('$web_logging.handler:'+action+':'+type_of_handler);

            handler(response);
        }

        // -----------------------------------------
        // Run default action (change LINE position)
        // -----------------------------------------

        else if (current_action == default_action)
        {
            $updateSublineData(current_action, response, props, total, status, path);
        }

        else if (action == '101') 
        {
            $ProfileClients.reset();
            $updateUserForm(data);
            $ProfileClients.update(response['profile_clients']);
            $updateUserPhoto(response['photo']);
            $getSettings(response['settings']);
            $getPrivileges(response['privileges']);
        }
        else if (['201','202'].indexOf(action) > -1) 
        {
            $StatusChangeDialog.open(action, data);
        }
        else if (action == default_log_action)
        {
            $updateLog(current_action, response);
        }
        else
        {
            $updateViewData(current_action, response, props, total, status, path);
        }

        is_loaded_success = true;

        $TriggerActions(false);

        $ShowLogPage();

        // --------------------
        // Run Callback Handler
        // --------------------

        if (isCallback) {
            isCallback = false;

            if (typeof log_callback === 'function')
                log_callback(current_action, data, props);
        }

    }, 'json')
    .fail(function() {
        is_loaded_success = false;
    })
    .always(function() {
        if (page_state == -1)
            page_state = 0;

        $ShowLoader(-1);
        $TriggerActions(false);
    });
}

