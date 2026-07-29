#include "boot.h"

#include "../assets/custom_fonts.h"

#define BOOT_FRAME_COUNT 5
#define BOOT_FRAME_PERIOD_MS 140
#define BOOT_FINAL_HOLD_MS 550

extern const lv_img_dsc_t boot_logo_0;
extern const lv_img_dsc_t boot_logo_1;
extern const lv_img_dsc_t boot_logo_2;
extern const lv_img_dsc_t boot_logo_3;
extern const lv_img_dsc_t boot_logo_4;

static const lv_img_dsc_t *boot_frames[BOOT_FRAME_COUNT] = {
    &boot_logo_0,
    &boot_logo_1,
    &boot_logo_2,
    &boot_logo_3,
    &boot_logo_4,
};

static lv_obj_t *boot_overlay;
static lv_obj_t *boot_image;
static lv_obj_t *maker_label;
static lv_obj_t *product_label;
static uint8_t boot_frame_index;

static void show_boot_text(void) {
    lv_obj_clear_flag(maker_label, LV_OBJ_FLAG_HIDDEN);
    lv_obj_clear_flag(product_label, LV_OBJ_FLAG_HIDDEN);
}

static void boot_timer_cb(lv_timer_t *timer) {
    if (++boot_frame_index < BOOT_FRAME_COUNT) {
        lv_img_set_src(boot_image, boot_frames[boot_frame_index]);

        if (boot_frame_index == BOOT_FRAME_COUNT - 1) {
            show_boot_text();
            lv_timer_set_period(timer, BOOT_FINAL_HOLD_MS);
        }
        return;
    }

    lv_timer_del(timer);
    lv_obj_del(boot_overlay);
    boot_overlay = NULL;
}

static lv_obj_t *create_centered_label(lv_obj_t *parent, const char *text, const lv_font_t *font,
                                       lv_coord_t y) {
    lv_obj_t *label = lv_label_create(parent);
    lv_obj_set_width(label, 144);
    lv_obj_set_style_text_color(label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(label, font, LV_PART_MAIN);
    lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_label_set_text(label, text);
    lv_obj_align(label, LV_ALIGN_TOP_MID, 0, y);
    lv_obj_add_flag(label, LV_OBJ_FLAG_HIDDEN);
    return label;
}

int zmk_widget_boot_init(lv_obj_t *parent) {
    boot_frame_index = 0;

    boot_overlay = lv_obj_create(parent);
    lv_obj_set_size(boot_overlay, 144, 168);
    lv_obj_align(boot_overlay, LV_ALIGN_TOP_LEFT, 0, 0);
    lv_obj_set_style_bg_color(boot_overlay, lv_color_black(), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(boot_overlay, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(boot_overlay, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(boot_overlay, 0, LV_PART_MAIN);
    lv_obj_clear_flag(boot_overlay, LV_OBJ_FLAG_SCROLLABLE);

    boot_image = lv_img_create(boot_overlay);
    lv_img_set_src(boot_image, boot_frames[0]);
    lv_obj_align(boot_image, LV_ALIGN_TOP_MID, 0, 2);

    maker_label = create_centered_label(boot_overlay, "beekeeb", &quinquefive_8, 106);
    product_label = create_centered_label(boot_overlay, "TOUCAN", &quinquefive_24, 124);

    lv_timer_create(boot_timer_cb, BOOT_FRAME_PERIOD_MS, NULL);
    return 0;
}
