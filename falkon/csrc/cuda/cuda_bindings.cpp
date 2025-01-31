#include "cuda_bindings.h"

#include <torch/extension.h>
#include <c10/cuda/CUDAStream.h>
#include <c10/cuda/CUDAException.h>

#include <c10/cuda/CUDAGuard.h>


std::pair<size_t, size_t> mem_get_info(int device_id) {
    const at::cuda::CUDAGuard device_guard(device_id);
    size_t free;
    size_t total;
    C10_CUDA_CHECK(cudaMemGetInfo(&free, &total));
    return std::pair<size_t, size_t>{free, total};
}


void cuda_2d_copy_async(
    torch::Tensor& dest_tensor,
    const int dest_pitch,
    const torch::Tensor& src_tensor,
    const int src_pitch,
    const int width,
    const int height,
    const at::cuda::CUDAStream &stream
)
{
    C10_CUDA_CHECK(cudaMemcpy2DAsync(
        dest_tensor.data_ptr(),
        dest_pitch,
        src_tensor.data_ptr(),
        src_pitch,
        width,
        height,
        cudaMemcpyDefault,
        stream.stream()
    ));
}

void cuda_2d_copy(
    torch::Tensor& dest_tensor,
    const int dest_pitch,
    const torch::Tensor& src_tensor,
    const int src_pitch,
    const int width,
    const int height
)
{

    C10_CUDA_CHECK(cudaMemcpy2D(
        dest_tensor.data_ptr(),
        dest_pitch,
        src_tensor.data_ptr(),
        src_pitch,
        width,
        height,
        cudaMemcpyDefault
    ));
}

void cuda_1d_copy_async(
    torch::Tensor& dest_tensor,
    const torch::Tensor &src_tensor,
    const int count,
    const at::cuda::CUDAStream &stream
)
{
    C10_CUDA_CHECK(cudaMemcpyAsync(
        dest_tensor.data_ptr(),
        src_tensor.data_ptr(),
        count,
        cudaMemcpyDefault,
        stream.stream()
    ));
}

void cuda_1d_copy(
    torch::Tensor& dest_tensor,
    const torch::Tensor &src_tensor,
    const int count
)
{
    C10_CUDA_CHECK(cudaMemcpy(
        dest_tensor.data_ptr(),
        src_tensor.data_ptr(),
        count,
        cudaMemcpyDefault
    ));
}

