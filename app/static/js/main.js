// **************************************
// APPLICATION PAGE DECLARATION: /main.js
// --------------------------------------
// Version: 1.00
// Date: 28-10-2022

default_submit_mode = 2;
default_action      = '700';
default_log_action  = '701';
default_input_name  = 'node_id';
default_menu_item   = '';

LINE    = '';
SUBLINE = '';

var postonline_path = null;

// ----------------------
// Dialog Action Handlers
// ----------------------

function sidebar_callback() {
    $onInfoContainerChanged();
}

function subline_refresh(filename) {
    $(".filename").each(function() { 
        $(this).html(filename);
    });
}

function log_callback(current_action, data, props) {
    batch_can_be_activated = (!is_empty(props) && 'activate' in props) ? props['activate'] : 0;
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['type', 'status', 'batchtype']);

    page_sort_title = $("#sort_icon").attr('title');

    SelectedReset();

    $TabSelector.init();

    tab_init('activities', 0);
    tab_init('reliabilities', 0);

    init_controller('activities');

    // ------------------------
    // Start default log action
    // ------------------------

    interrupt(true, 1);
}

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    function _check(x) { 
        var errors = x['errors']; 

        //alert(errors.length);

        if (errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
        }
        else {
            $NotificationDialog.open(keywords['Message:Request sent successfully']);
        }
    }

    switch (mode) {
        case 0:
            break;
        case 1:
            if (confirm_action == 'activate') {
                var ids = SelectedGetItem(SUBLINE, 'id');

                $("input[name='selected_batch_ids']").each(function() { $(this).val(ids); });
                $("#command").val('admin:'+confirm_action);

                $onParentFormSubmit();
            }
    }
}

function $Notification(mode, ob) {
    $NotificationDialog.close();
}

function $onTabSelect(group){
    $MainSubmitDialog.activate(group);
}

function $onTablineSelect(ob, alias) {
}

function $onTablineUpload(alias) {
    //alert('$onTablineUpload.alias:'+alias);
    $Go('702');
    return 1;
}

function $onPaginationFormSubmit(frm) {
    return true;
}

function $onFilterFormSubmit(frm) {
    return true;
}

function $onInfoContainerChanged() {
    //alert($_width('screen-min')-$("#sidebarFrame").width()+':'+$("#line-table").width());
}

function $onTabSelect(ob) {
    return true;
}

// ===========================
// Dialog windows declarations
// ===========================

function MakeFilterSubmit(mode, page) {
    //$("#filter-form").attr("action", baseURI);

    switch (mode) {

        // -------------
        // Submit modes:
        // -------------

        case 0:
        case 1:
        case 2:
            var division = $("select#division").val();
            $("input[name='division']").each(function() { $(this).val(division); });
        case 3:
            var line = $("select#line").val();
            $("input[name='line']").each(function() { $(this).val(line); });
        case 4:
        case 5:
            break;

        // ---------------------------
        // LineSelector Handler submit
        // ---------------------------

        case 9:
    }

    $ResetLogPage();

    $setPaginationFormSubmit(page);
    $onParentFormSubmit('filter-form');
}

function makeTodayRequest() {
    var date = new Date();
    var now = date.getToday();

    $_set_body_value('order-date-from', now);
    $onParentFormSubmit('filter-form');
}


// =========================
// Custom routine assigments
// =========================

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{

    // -------------
    // Client events
    // -------------

    $("#period", this).on("click", function(e) {
        e.stopPropagation();
        //
        //  Show Diagram Node info
        //
        var ob = $(this);
        $PageController.show_period("over");
        //alert('click1:'+ob.attr('id'));
        e.stopPropagation();
    });

    $("div.nodeinline").contextmenu(function(e) {
        e.stopPropagation();
        $PageController.show_contextmenu($(this), e, "open");
        if (IsHideContextMenu) {
            //alert( "Handler for diagram item.contextmenu() called." );
        }
        e.preventDefault();
        return false;
    });

    $(".nodeinline").on("click", function(e) {
        e.stopPropagation();
        //
        //  Show Diagram Node info
        //
        var ob = $(this);
        $PageController.show_info_node(ob, "over");
        if ($_mobile())
            $PageController.show_contextmenu($(this), e, "open");
        //alert('click1');
    });

    $("#diagram", this).on("click", function(e) {
        e.stopPropagation();
        //
        //  Show Diagram Line
        //
        var ob = $(this);
        $PageController.show_info_node(ob, "out");
        $PageController.show_contextmenu(ob, e, "close");
        //alert('click2');
    });

    // ---------------------
    // Data Section progress
    // ---------------------

    // -----------------
    // Tabline selection
    // -----------------

    $(".column").on('click', function(e) {
        if (!$_mobile())
            return;

        e.stopPropagation();

        var ob = ($(this)).parent();
        var id = ob.attr('id');

        if (IsTrace)
            alert('mobile.click.column:'+id);

        $PageScroller.init_state(ob);

        if (id.indexOf('reliabilities') > -1 || id.indexOf('activities') > -1)
            $PageController.show_line(ob, true, 1);
    });

    $("#data-section").on('click', '.column', function(e) {
        //
        //  Tabline Columns click
        //
        var ob = ($(this)).parent();
        var id = ob.attr('id');

        if (IsTrace)
            alert('main.click.column:'+id);

        $PageScroller.init_state(ob);

        if (id.indexOf('reliabilities') > -1 || id.indexOf('activities') > -1)
            $PageController.show_line(ob, true, 0);
    });

    $("#data-section").on('click', '.row-button', function(e) {
        //
        //  Tabline Navigate Buttons Cursor Controller click
        //
        e.stopPropagation();

        var ob = $(this).children('a').eq(0);
        var id = ob.attr('id');
        var link = id.split(':')[1];
        var x = link.split('_');
        var group = x[0];
        var command = x[1];

        if (IsTrace)
            alert('main.click.row-button:'+joinToPrint([group, command]));

        $PageScroller.refresh(group, command);

        e.preventDefault();

    });

    // -----------------
    // Page Form Buttons
    // -----------------

    $("a[id^='menu_']", this).click(function(e) {
        //
        //  Contextmenu Item activated
        //
        var ob = ($(this));
        var id = ob.attr('id');
        
        $PageController.contextmenu_activated(ob);
        e.preventDefault();
        e.stopPropagation();
    });

    $("button[id^='page']", this).click(function(e) {
        $PageButton($(this));
        e.preventDefault();
    });

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $PageScroller.reset(1, 1000);
    });

    $(window).scroll(function(e){
        //$PageScroller.checkPosition(0);
    });

    // --------
    // Keyboard
    // --------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        if (is_show_error)
            return;

        if (e.keyCode==13) {                                     // Enter
            // --------------------------------------
            // Application Submit Dialog Class Events
            // --------------------------------------
            if ($MainSubmitDialog.is_focused()) {
                $MainSubmitDialog.confirmed();
                e.preventDefault();
                return false;
            }
        }

        if ($MainSubmitDialog.is_focused() || is_search_focused)
            return;

        var exit = false;

        if (IsTrace && IsDeepDebug)
            alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        exit = true;
        
        if (e.shiftKey && e.keyCode==9)                          // Shift-Tab
            init_controller(null);

        if (e.shiftKey && e.keyCode==80) {                       // Shift-P
            exit = true;
        }

        if (e.shiftKey && [67, 79].indexOf(e.keyCode) > -1) {    // Shift-C,Shift-O
            e.stopPropagation();
            if (IsSidebarEnabled)
                $SidebarDialog.activate($(this));
            exit = true;
        }
        
        // -----------------------
        // Tabline Selector moving
        // -----------------------

        else if (selector.active) {
            if (e.keyCode==38)                                  // Up
                $PageScroller.refresh(null, 'up');
            else if (e.keyCode==40)                             // Down
                $PageScroller.refresh(null, 'down');
            else if (e.keyCode==36)                             // Home
                $PageScroller.refresh(null, 'first');
            else if (e.keyCode==33)                             // PgUp
                $PageScroller.refresh(null, 'pgup');
            else if (e.keyCode==34)                             // PgDown
                $PageScroller.refresh(null, 'pgdown');
            else if (e.keyCode==35)                             // End
                $PageScroller.refresh(null, 'last');
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function page_is_focused(e) {
    return $MainSubmitDialog.is_focused();
}

function $_show_page(mode) {
    $ShowPage(mode);
}

function resize(force) {
    if ($_mobile() && force) {
        //show_width();
        //show_height();

        var viewportW = verge.viewportW();
        var viewportH = verge.viewportH();

        //alert(viewportW+':'+ viewportH);
    }
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (main)');

    IsLog = 1;
    IsDebug = 0;
    IsDeepDebug = 0;
    IsTrace = 0;

    current_context = 'main';

    if (!is_empty(search_title))
        $("#search-context").attr("placeholder", search_title);
    //$("#batchtype").css("width", $("#status").width()+"px");
    //$("#batchtype").width($("#status").width());

    $PageController._init_state();

    IsActiveScroller = 0;
    IsSidebarEnabled = 1;

    resize(1);

    $_init();
});
