<?php
/**
 * Plugin Name: DROPIFY Fulfillment AI
 * Plugin URI: https://github.com/HardbanRecordsLab/Dropify-Service
 * Description: Sprint-4 integration (#9, doku/PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md). One click on a WooCommerce product
 *              posts an AI-matched DROPIFY job (photography, listing copy, video, fulfillment...) via the White-Label
 *              Reseller API (see backend/app/routes/developer.py). No DROPIFY account credentials are ever stored here
 *              beyond the single partner API key you generate in your own DROPIFY dashboard (Developer / API).
 * Version: 1.0.0
 * Requires Plugins: woocommerce
 * Author: HardbanRecords Lab (DROPIFY)
 * License: MIT
 * Text Domain: dropify-fulfillment-ai
 */

if (!defined('ABSPATH')) {
    exit; // no direct access
}

define('DROPIFY_FAI_VERSION', '1.0.0');
define('DROPIFY_FAI_OPTION', 'dropify_fai_settings');
define('DROPIFY_FAI_META_JOB_ID', '_dropify_job_id');
define('DROPIFY_FAI_META_STATUS', '_dropify_job_status');

/**
 * Settings: DROPIFY API base URL + partner API key (Developer / White-label
 * API page in the DROPIFY dashboard -> "Create API key").
 */
function dropify_fai_settings(): array
{
    $defaults = [
        'api_url' => 'https://api.dropify.app/api',
        'api_key' => '',
        'auto_create_on_publish' => '0',
        'default_budget' => '500',
    ];
    return wp_parse_args(get_option(DROPIFY_FAI_OPTION, []), $defaults);
}

add_action('admin_menu', function () {
    add_options_page(
        'DROPIFY Fulfillment AI',
        'DROPIFY Fulfillment AI',
        'manage_options',
        'dropify-fai',
        'dropify_fai_settings_page'
    );
});

function dropify_fai_settings_page(): void
{
    if (!current_user_can('manage_options')) {
        return;
    }
    if (isset($_POST['dropify_fai_save']) && check_admin_referer('dropify_fai_settings')) {
        update_option(DROPIFY_FAI_OPTION, [
            'api_url' => esc_url_raw(rtrim(sanitize_text_field($_POST['api_url'] ?? ''), '/')),
            'api_key' => sanitize_text_field($_POST['api_key'] ?? ''),
            'auto_create_on_publish' => isset($_POST['auto_create_on_publish']) ? '1' : '0',
            'default_budget' => absint($_POST['default_budget'] ?? 500),
        ]);
        echo '<div class="updated"><p>Saved.</p></div>';
    }
    $s = dropify_fai_settings();
    ?>
    <div class="wrap">
        <h1>DROPIFY Fulfillment AI</h1>
        <p>Connect this store to your DROPIFY White-Label API key (DROPIFY dashboard &rarr; <em>Developer / API</em> &rarr;
            <em>Create API key</em>). One product = one AI-matched DROPIFY job.</p>
        <form method="post">
            <?php wp_nonce_field('dropify_fai_settings'); ?>
            <table class="form-table">
                <tr>
                    <th><label for="api_url">DROPIFY API URL</label></th>
                    <td><input type="url" id="api_url" name="api_url" class="regular-text"
                               value="<?php echo esc_attr($s['api_url']); ?>" required></td>
                </tr>
                <tr>
                    <th><label for="api_key">Partner API key</label></th>
                    <td><input type="password" id="api_key" name="api_key" class="regular-text"
                               value="<?php echo esc_attr($s['api_key']); ?>" placeholder="dpk_..." required></td>
                </tr>
                <tr>
                    <th><label for="default_budget">Default job budget (PLN)</label></th>
                    <td><input type="number" id="default_budget" name="default_budget" min="50" step="10"
                               value="<?php echo esc_attr($s['default_budget']); ?>"></td>
                </tr>
                <tr>
                    <th>Auto-create on publish</th>
                    <td>
                        <label>
                            <input type="checkbox" name="auto_create_on_publish" value="1"
                                <?php checked($s['auto_create_on_publish'], '1'); ?>>
                            Automatically post a DROPIFY job whenever a new product is published
                        </label>
                    </td>
                </tr>
            </table>
            <?php submit_button('Save settings', 'primary', 'dropify_fai_save'); ?>
        </form>
    </div>
    <?php
}

/**
 * Core: create a DROPIFY job for a WooCommerce product via the White-Label API.
 */
function dropify_fai_create_job(int $product_id): array
{
    $settings = dropify_fai_settings();
    if (empty($settings['api_key']) || empty($settings['api_url'])) {
        return ['error' => 'DROPIFY API not configured (Settings -> DROPIFY Fulfillment AI).'];
    }
    $product = wc_get_product($product_id);
    if (!$product) {
        return ['error' => 'Product not found.'];
    }

    $body = [
        'title' => sprintf('Fulfillment content: %s', $product->get_name()),
        'description' => wp_strip_all_tags($product->get_description() ?: $product->get_short_description())
            ?: sprintf('WooCommerce product "%s" (SKU: %s) needs fulfillment content (photos, listing copy, video).', $product->get_name(), $product->get_sku()),
        'budget' => (float) $settings['default_budget'],
        'deadline' => gmdate('Y-m-d', strtotime('+10 days')),
        'location' => '',
        'required_skills' => ['e-commerce', 'photography'],
    ];

    $response = wp_remote_post(rtrim($settings['api_url'], '/') . '/v1/external/jobs', [
        'headers' => [
            'Content-Type' => 'application/json',
            'X-Api-Key' => $settings['api_key'],
        ],
        'body' => wp_json_encode($body),
        'timeout' => 15,
    ]);

    if (is_wp_error($response)) {
        return ['error' => $response->get_error_message()];
    }
    $code = wp_remote_retrieve_response_code($response);
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if ($code !== 200 || empty($data['job_id'])) {
        return ['error' => $data['detail'] ?? 'DROPIFY API error (HTTP ' . $code . ')'];
    }

    update_post_meta($product_id, DROPIFY_FAI_META_JOB_ID, sanitize_text_field($data['job_id']));
    update_post_meta($product_id, DROPIFY_FAI_META_STATUS, 'open');
    return ['job_id' => $data['job_id']];
}

/** Auto-create on publish, if enabled. */
add_action('woocommerce_process_product_meta', function (int $product_id) {
    $settings = dropify_fai_settings();
    if ($settings['auto_create_on_publish'] !== '1') {
        return;
    }
    if (get_post_meta($product_id, DROPIFY_FAI_META_JOB_ID, true)) {
        return; // already created
    }
    dropify_fai_create_job($product_id);
});

/** Product-edit meta box: manual "Create DROPIFY job" button + live status. */
add_action('add_meta_boxes', function () {
    add_meta_box(
        'dropify_fai_box',
        'DROPIFY Fulfillment AI',
        'dropify_fai_render_meta_box',
        'product',
        'side',
        'default'
    );
});

function dropify_fai_render_meta_box(WP_Post $post): void
{
    $job_id = get_post_meta($post->ID, DROPIFY_FAI_META_JOB_ID, true);
    $status = get_post_meta($post->ID, DROPIFY_FAI_META_STATUS, true);
    wp_nonce_field('dropify_fai_action', 'dropify_fai_nonce');
    if ($job_id) {
        printf(
            '<p>Job: <code>%s</code><br>Status: <strong>%s</strong></p><p><button type="submit" name="dropify_fai_resync" class="button">Refresh status</button></p>',
            esc_html($job_id),
            esc_html($status ?: 'unknown')
        );
    } else {
        echo '<p>No DROPIFY job yet for this product.</p>';
        echo '<p><button type="submit" name="dropify_fai_create" class="button button-primary">Create DROPIFY job</button></p>';
    }
}

/** Handle the meta-box button clicks on product save. */
add_action('save_post_product', function (int $post_id) {
    if (!isset($_POST['dropify_fai_nonce']) || !wp_verify_nonce($_POST['dropify_fai_nonce'], 'dropify_fai_action')) {
        return;
    }
    if (!current_user_can('edit_post', $post_id)) {
        return;
    }

    if (isset($_POST['dropify_fai_create'])) {
        dropify_fai_create_job($post_id);
    }

    if (isset($_POST['dropify_fai_resync'])) {
        $job_id = get_post_meta($post_id, DROPIFY_FAI_META_JOB_ID, true);
        $settings = dropify_fai_settings();
        if ($job_id && $settings['api_url']) {
            // GET /api/jobs/{id} is a public, unauthenticated read on the DROPIFY API.
            $response = wp_remote_get(rtrim($settings['api_url'], '/') . '/jobs/' . rawurlencode($job_id), ['timeout' => 10]);
            if (!is_wp_error($response)) {
                $data = json_decode(wp_remote_retrieve_body($response), true);
                if (!empty($data['status'])) {
                    update_post_meta($post_id, DROPIFY_FAI_META_STATUS, sanitize_text_field($data['status']));
                }
            }
        }
    }
});
