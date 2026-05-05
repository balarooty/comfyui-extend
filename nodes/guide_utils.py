def make_noise_mask(latent, samples):
    import torch

    if "noise_mask" in latent:
        return latent["noise_mask"].clone()

    batch, _, latent_frames, _, _ = samples.shape
    return torch.ones(
        (batch, 1, latent_frames, 1, 1),
        dtype=torch.float32,
        device=samples.device,
    )


def pixel_frame_count_from_latent(latent_frames, scale_factors):
    time_scale_factor = scale_factors[0]
    return (latent_frames - 1) * time_scale_factor + 1


def resolve_frame_index(frame_index, pixel_frame_count):
    if frame_index < 0:
        return pixel_frame_count + frame_index
    return frame_index


def add_ltx_guide(positive, negative, vae, latent_image, noise_mask, image, frame_index, strength):
    from comfy_extras.nodes_lt import LTXVAddGuide

    scale_factors = vae.downscale_index_formula
    _, _, latent_length, latent_height, latent_width = latent_image.shape

    resolved_index = resolve_frame_index(frame_index, pixel_frame_count_from_latent(latent_length, scale_factors))
    _, encoded = LTXVAddGuide.encode(vae, latent_width, latent_height, image, scale_factors)
    guide_frame_idx, latent_idx = LTXVAddGuide.get_latent_index(
        positive,
        latent_length,
        image.shape[0],
        resolved_index,
        scale_factors,
    )

    if latent_idx >= latent_length:
        raise ValueError(
            f"Guide frame {frame_index} resolves to latent index {latent_idx}, "
            f"but latent length is only {latent_length}."
        )

    if latent_idx + encoded.shape[2] > latent_length:
        encoded = encoded[:, :, : latent_length - latent_idx]

    return LTXVAddGuide.append_keyframe(
        positive,
        negative,
        guide_frame_idx,
        latent_image,
        noise_mask,
        encoded,
        strength,
        scale_factors,
    )
