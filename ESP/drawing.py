import flameclient.esp.globals as main;

_debug_fill_failures = 0

def _get_gui_layer():
    cls = getattr(main, "gui_layer_class", None)
    if cls is None:
        return None
    # Try common static accessors.
    for method in ("gui", "getGui"):
        try:
            fn = getattr(cls, method)
            return fn()
        except:
            pass
    return None

def _try_fill_reflection(draw_context, start_x, start_y, end_x, end_y, color):
    try:
        methods = draw_context.getClass().getMethods()
        layer = _get_gui_layer()
        for m in methods:
            try:
                if m.getName() != "fill":
                    continue
                pc = m.getParameterCount()
                if pc == 5:
                    m.invoke(draw_context,
                             main.j_integer(int(start_x)),
                             main.j_integer(int(start_y)),
                             main.j_integer(int(end_x)),
                             main.j_integer(int(end_y)),
                             main.j_integer(int(color)))
                    return True
                if pc == 6 and layer is not None:
                    m.invoke(draw_context,
                             layer,
                             main.j_integer(int(start_x)),
                             main.j_integer(int(start_y)),
                             main.j_integer(int(end_x)),
                             main.j_integer(int(end_y)),
                             main.j_integer(int(color)))
                    return True
            except:
                pass
    except:
        pass
    return False

def _get_pose(draw_context):
    # Different versions expose different matrix-stack getters.
    for getter in ("pose", "getMatrices", "matrices"):
        try:
            fn = getattr(draw_context, getter)
            return fn()
        except:
            pass
    return None

def _push_pose(pose):
    for method in ("pushMatrix", "pushPose", "push"):
        try:
            getattr(pose, method)()
            return
        except:
            pass

def _pop_pose(pose):
    for method in ("popMatrix", "popPose", "pop"):
        try:
            getattr(pose, method)()
            return
        except:
            pass

def _scale_pose(pose, scale):
    for method in ("scale",):
        try:
            getattr(pose, method)(scale, scale, 1.0)
            return True
        except:
            pass
    return False

def _draw_string(draw_context, text_str, x, y, color):
    # Try a few common DrawContext text methods.
    try:
        draw_context.drawString(main.FONT, text_str, int(x), int(y), color)
        return True
    except:
        pass
    try:
        draw_context.drawTextWithShadow(main.FONT, text_str, int(x), int(y), color)
        return True
    except:
        pass
    try:
        # Some mappings expose drawText; extra params vary, so keep it minimal.
        draw_context.drawText(main.FONT, text_str, int(x), int(y), color, True)
        return True
    except:
        pass
    return False

def text(draw_context, text_str, x, y, color):
    scale = main.SETTINGS.get("TEXT_SCALE", 1.0)
    
    if scale == 1.0:
        _draw_string(draw_context, text_str, x, y, color);
    else:
        pose = _get_pose(draw_context)
        if pose is None:
            _draw_string(draw_context, text_str, x, y, color)
            return

        _push_pose(pose)
        if _scale_pose(pose, scale):
            _draw_string(draw_context, text_str, (x / scale), (y / scale), color)
        else:
            _draw_string(draw_context, text_str, x, y, color)
        _pop_pose(pose)

def outline_text(draw_context, tstr, x, y, color):
    outline = main.COLORS.get("TEXT_OUTLINE_COLOR", "#B3000000"); # Use outline color from config
    offset = main.SETTINGS.get("OUTLINE_OFFSET", 1.0)

    text(draw_context, tstr, x - offset, y, outline);
    text(draw_context, tstr, x + offset, y, outline);
    text(draw_context, tstr, x, y - offset, outline);
    text(draw_context, tstr, x, y + offset, outline);
    
    text(draw_context, tstr, x, y, color);

def filled_rect(draw_context, start_x, start_y, end_x, end_y, color):    
    start_x, start_y = int(start_x), int(start_y);
    end_x, end_y = int(end_x), int(end_y);

    # DrawContext.fill overloads differ across versions.
    try:
        draw_context.fill(start_x, start_y, end_x, end_y, int(color));
        return
    except:
        pass

    layer = _get_gui_layer()
    if layer is not None:
        try:
            draw_context.fill(layer, start_x, start_y, end_x, end_y, int(color));
            return
        except:
            pass

    ok = _try_fill_reflection(draw_context, start_x, start_y, end_x, end_y, int(color))
    if ok:
        return

    # Throttled diagnostics: print DrawContext type + fill overloads.
    global _debug_fill_failures
    if main.SETTINGS.get("DEBUG_MODE", False):
        _debug_fill_failures = _debug_fill_failures + 1
        if _debug_fill_failures % 300 == 0:
            try:
                cls = draw_context.getClass()
                name = cls.getName()
                layer = _get_gui_layer()
                sigs = []
                try:
                    for m in cls.getMethods():
                        if m.getName() != "fill":
                            continue
                        sigs.append(str(m.getParameterCount()))
                except:
                    pass
                try:
                    main.echo("[flameclient] DrawContext=" + str(name) + " fillOverloads=" + ",".join(sigs) + " layer=" + ("yes" if layer is not None else "no"))
                except:
                    pass
            except:
                pass

def parse_color(color):
    if isinstance(color, str):
        if color.startswith("#"):
            color = color[1:]
        val = int(color, 16)
        if val > 0x7FFFFFFF:
            val -= 0x100000000
        return val
    return color

def filled_gradient(draw_context, start_x, start_y, end_x, end_y, upper, lower):
    start_x, start_y = int(start_x), int(start_y);
    end_x, end_y = int(end_x), int(end_y);

    upper = parse_color(upper)
    lower = parse_color(lower)

    # Force Java Integer to avoid Long inference
    upper = main.j_integer(int(upper))
    lower = main.j_integer(int(lower))

    draw_context.fillGradient(start_x, start_y, end_x, end_y, upper, lower);

def rect(draw_context, start_x, start_y, end_x, end_y, color):
    filled_rect(draw_context, start_x, start_y, end_x, start_y + 1, color);
    filled_rect(draw_context, start_x, end_y - 1, end_x, end_y, color);
    filled_rect(draw_context, start_x, start_y, start_x + 1, end_y, color);
    filled_rect(draw_context, end_x - 1, start_y, end_x, end_y, color);

def new(draw_type, *args):
    global callbacks;

    if (draw_type not in callbacks): 
        return; 

    return callbacks[draw_type](*args);

callbacks = {"outline_text": outline_text, "text": text, "filled_rect": filled_rect, "filled_gradient": filled_gradient, "rect": rect};
